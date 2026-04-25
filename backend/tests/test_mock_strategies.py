"""
Tests for the three differentiated mock agent strategies.

Each strategy must:

1. Patch ``app/main.py`` and write ``app/rate_limit.py`` inside a real
   PulseDesk-shaped worktree.
2. Produce valid Python (parses with ``ast``).
3. Be idempotent (apply twice == apply once).
4. Make all rate-limit acceptance tests pass when run inside the patched copy.

The end-to-end assertion uses the backend's already-provisioned Python
environment (``sys.executable``) — demo-repo's runtime deps (fastapi,
jinja2, httpx) are pinned in ``backend/pyproject.toml`` dev-deps so we
don't need to ``uv sync`` inside each tmp copy.

If a future demo-repo dep is missing from the backend env, the e2e tests
fail loudly with the import error (per ``/implement``: no silent fallbacks).
"""
from __future__ import annotations

import ast
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from app.agent_runner.mock_runner import _apply_rate_limiting

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_REPO_SRC = REPO_ROOT / "demo-repo"

STRATEGIES = ("route_local", "dependency", "middleware")

# Markers each strategy must inject into ``app/main.py``. Used as cheap
# "did we land in the right place" assertions; the AST parse below is the
# correctness gate.
STRATEGY_MARKERS: dict[str, str] = {
    "route_local": "from .rate_limit import check_rate_limit",
    "dependency": "Depends(enforce_login_rate_limit)",
    "middleware": "app.add_middleware(RateLimitMiddleware)",
}


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def pulsedesk_copy(tmp_path: Path) -> Path:
    """Fresh copy of ``demo-repo`` at ``tmp_path/pulsedesk``, on ``main``.

    Excludes the lockable / regenerable bits (``.git``, ``.venv``, caches,
    seeded SQLite) so the copy is deterministic per test.
    """
    if not (DEMO_REPO_SRC / "app" / "main.py").exists():
        pytest.skip("demo-repo not present at expected path; cannot exercise mock strategies")

    target = tmp_path / "pulsedesk"
    shutil.copytree(
        DEMO_REPO_SRC,
        target,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            "*.pyc",
            "data",
            ".pytest_cache",
        ),
    )
    _git(["init", "-b", "main"], target)
    _git(["config", "user.email", "test@agent-graph.test"], target)
    _git(["config", "user.name", "Test"], target)
    _git(["add", "."], target)
    _git(["commit", "-m", "init"], target)
    return target


def _ensure_demo_runtime_deps_importable() -> None:
    """Fail fast (with an actionable hint) if the backend env is missing
    a runtime dep that demo-repo's ``app.main`` imports at module load."""
    missing: list[str] = []
    for module in ("fastapi", "jinja2", "httpx"):
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    if missing:
        pytest.fail(
            f"Backend test env is missing demo-repo runtime deps: {missing}. "
            "Add them to backend/pyproject.toml [dependency-groups].dev and "
            "re-run `uv sync`."
        )


# ── Structural assertions (cheap; always run) ──────────────────────────────────


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_strategy_writes_rate_limit_module_and_patches_main(
    pulsedesk_copy: Path, strategy: str
) -> None:
    applied = _apply_rate_limiting(str(pulsedesk_copy), strategy=strategy)
    assert applied is True, f"strategy={strategy!r} failed to apply against the demo-repo copy"

    rate_limit_py = pulsedesk_copy / "app" / "rate_limit.py"
    assert rate_limit_py.exists(), f"strategy={strategy!r} did not write app/rate_limit.py"

    main_py_text = (pulsedesk_copy / "app" / "main.py").read_text(encoding="utf-8")
    assert STRATEGY_MARKERS[strategy] in main_py_text, (
        f"strategy={strategy!r} did not insert marker {STRATEGY_MARKERS[strategy]!r} into app/main.py"
    )


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_strategy_produces_valid_python(pulsedesk_copy: Path, strategy: str) -> None:
    _apply_rate_limiting(str(pulsedesk_copy), strategy=strategy)

    main_py_text = (pulsedesk_copy / "app" / "main.py").read_text(encoding="utf-8")
    rate_limit_py_text = (pulsedesk_copy / "app" / "rate_limit.py").read_text(encoding="utf-8")

    # ast.parse raises SyntaxError on malformed substitution — the regression
    # we most fear from string-based patching.
    ast.parse(main_py_text)
    ast.parse(rate_limit_py_text)


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_strategy_is_idempotent(pulsedesk_copy: Path, strategy: str) -> None:
    _apply_rate_limiting(str(pulsedesk_copy), strategy=strategy)
    main_after_first = (pulsedesk_copy / "app" / "main.py").read_text(encoding="utf-8")
    rate_limit_after_first = (pulsedesk_copy / "app" / "rate_limit.py").read_text(encoding="utf-8")

    _apply_rate_limiting(str(pulsedesk_copy), strategy=strategy)
    main_after_second = (pulsedesk_copy / "app" / "main.py").read_text(encoding="utf-8")
    rate_limit_after_second = (pulsedesk_copy / "app" / "rate_limit.py").read_text(encoding="utf-8")

    assert main_after_first == main_after_second
    assert rate_limit_after_first == rate_limit_after_second


def test_unknown_strategy_falls_back_to_default(pulsedesk_copy: Path) -> None:
    """Unknown strategy names degrade to the route-local default rather than crash."""
    applied = _apply_rate_limiting(str(pulsedesk_copy), strategy="not-a-real-strategy")  # type: ignore[arg-type]
    assert applied is True
    main_py_text = (pulsedesk_copy / "app" / "main.py").read_text(encoding="utf-8")
    assert STRATEGY_MARKERS["route_local"] in main_py_text


# ── End-to-end behavioural assertion (requires uv on PATH) ─────────────────────


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_strategy_makes_rate_limit_tests_pass(
    pulsedesk_copy: Path, strategy: str
) -> None:
    """Apply the patch then run the rate-limit acceptance suite inside the copy.

    This is the demo-critical assertion: each strategy must take the
    intentionally-failing tests in ``demo-repo/tests/test_rate_limit.py`` to
    green. If this fails, the demo's branch comparison shows a broken winner.

    Uses the backend's already-provisioned Python instead of ``uv sync``
    inside each copy — see module docstring for the env contract.
    """
    _ensure_demo_runtime_deps_importable()
    _apply_rate_limiting(str(pulsedesk_copy), strategy=strategy)

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_rate_limit.py", "-q", "--no-header"],
        cwd=str(pulsedesk_copy),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, (
        f"strategy={strategy!r} did not make the acceptance tests pass.\n"
        f"--- stdout ---\n{proc.stdout}\n"
        f"--- stderr ---\n{proc.stderr}"
    )
