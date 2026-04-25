"""
Shared test fixtures.

The ``isolated_backend`` fixture is the elegant answer to backend tests
fighting cached singletons (``get_settings``, ``graph_state``, ``task_manager``,
``event_bus``). It:

- spins up a fresh temp git repo on ``main``
- monkey-patches ``AGENT_GRAPH_*`` env vars to point at it
- clears the cached ``Settings``
- resets every module-global singleton via its ``reset_for_tests`` hook

Tests opt in by adding ``isolated_backend`` to their parameter list. The
fixture yields the temp repo path so tests can do filesystem assertions on it.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture(params=["asyncio"])
def anyio_backend(request):
    return request.param


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def isolated_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Backend talks to a fresh temp git repo; cached state is reset for the test."""
    repo = tmp_path / "demo-repo"
    repo.mkdir()
    _git(["init", "-b", "main"], repo)
    _git(["config", "user.email", "test@agent-graph.test"], repo)
    _git(["config", "user.name", "Agent Graph Test"], repo)
    (repo / "README.md").write_text("# isolated demo repo\n")
    _git(["add", "."], repo)
    _git(["commit", "-m", "init"], repo)

    monkeypatch.setenv("AGENT_GRAPH_DEMO_REPO_PATH", str(repo))
    monkeypatch.setenv("AGENT_GRAPH_BASE_BRANCH", "main")
    monkeypatch.setenv("AGENT_GRAPH_ENABLE_REAL_RUNS", "false")
    monkeypatch.setenv("AGENT_GRAPH_ENABLE_EVAL", "false")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    from app.settings import get_settings
    from app.state import graph_state
    from app.task_manager import task_manager
    from app.events import event_bus

    get_settings.cache_clear()
    graph_state.reset_for_tests()
    task_manager.reset_for_tests()
    event_bus.reset_for_tests()

    yield repo

    get_settings.cache_clear()
    graph_state.reset_for_tests()
    task_manager.reset_for_tests()
    event_bus.reset_for_tests()
