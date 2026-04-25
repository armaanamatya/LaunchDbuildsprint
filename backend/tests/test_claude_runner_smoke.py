"""
Real Claude SDK smoke test (P2-H).

Double-gated to avoid accidental API spend:
- ``ANTHROPIC_API_KEY`` must be set
- ``AGENT_GRAPH_RUN_REAL_SMOKE`` must be set to a truthy value

If both are present, the test exercises ``ClaudeAgentRunner`` end-to-end
against a real copy of the demo-repo to verify:

- The SDK returns at least one ``agent_text`` event.
- The SDK invokes the ``Read`` tool (it cannot solve the task without
  reading the codebase).
- The terminal event is ``agent_completed``.
- The agent actually wrote ``app/rate_limit.py`` (smoke confirmation that
  ``cwd``/permissions/system-prompt are wired correctly).

Run with::

    ANTHROPIC_API_KEY=sk-... AGENT_GRAPH_RUN_REAL_SMOKE=1 \
        uv run pytest tests/test_claude_runner_smoke.py -v
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_REPO_SRC = REPO_ROOT / "demo-repo"


pytestmark = pytest.mark.anyio


def _smoke_enabled() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY")) and bool(
        os.environ.get("AGENT_GRAPH_RUN_REAL_SMOKE")
    )


pytestmark_skip = pytest.mark.skipif(
    not _smoke_enabled(),
    reason="set ANTHROPIC_API_KEY and AGENT_GRAPH_RUN_REAL_SMOKE=1 to run the real Claude smoke test",
)


@pytest.fixture
def pulsedesk_copy(tmp_path: Path) -> Path:
    """Fresh copy of demo-repo on `main`. See test_mock_strategies.py for shape."""
    if not (DEMO_REPO_SRC / "app" / "main.py").exists():
        pytest.skip("demo-repo not present")

    target = tmp_path / "pulsedesk"
    shutil.copytree(
        DEMO_REPO_SRC,
        target,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", "__pycache__", "*.pyc", "data", ".pytest_cache",
        ),
    )

    def _git(args: list[str]) -> None:
        subprocess.run(
            ["git", *args], cwd=str(target), check=True, capture_output=True, text=True
        )

    _git(["init", "-b", "main"])
    _git(["config", "user.email", "test@agent-graph.test"])
    _git(["config", "user.name", "Agent Graph Smoke"])
    _git(["add", "."])
    _git(["commit", "-m", "init"])
    return target


@pytestmark_skip
async def test_claude_runner_completes_real_rate_limit_task(pulsedesk_copy: Path) -> None:
    from app.agent_runner.claude_runner import ClaudeAgentRunner
    from app.agent_runner.base import NormalizedEvent

    runner = ClaudeAgentRunner()
    events: list[NormalizedEvent] = []
    prompt = (
        "Add rate limiting to POST /api/login. Allow up to 5 attempts per IP per "
        "60 seconds. Return HTTP 429 with a Retry-After header. Successful logins "
        "count toward the limit. The acceptance tests are in tests/test_rate_limit.py."
    )

    async for event in runner.stream(
        node_id="smoke-1",
        prompt=prompt,
        worktree_path=str(pulsedesk_copy),
        strategy="route_local",
    ):
        events.append(event)
        # Hard cap: anything past 200 events is a runaway and we should bail.
        if len(events) > 200:
            pytest.fail(f"Claude runner produced >200 events without terminating; last: {event}")

    types = [e.type for e in events]
    assert "agent_text" in types, "Claude run should produce at least one text message"
    assert "agent_tool_use" in types, "Claude run should invoke at least one tool"
    assert types[-1] in ("agent_completed", "agent_failed"), (
        f"unexpected terminal event: {types[-1]}"
    )
    assert types[-1] == "agent_completed", (
        f"smoke run failed: last event content = "
        f"{events[-1].content!r}"
    )

    # File-on-disk smoke: the agent must have actually written rate_limit.py.
    rate_limit_py = pulsedesk_copy / "app" / "rate_limit.py"
    assert rate_limit_py.exists(), "Claude run should have created app/rate_limit.py"
