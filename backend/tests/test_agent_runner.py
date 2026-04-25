"""
Tests for the agent runner layer (Milestone 3).

Mock runner tests run without any API key.
Claude runner tests run only when AGENT_GRAPH_ENABLE_REAL_RUNS=true and ANTHROPIC_API_KEY is set.
"""
from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import pytest

from app.agent_runner.base import NormalizedEvent
from app.agent_runner.mock_runner import MockAgentRunner, _apply_rate_limiting, _git_commit
from app.task_manager import TaskManager


# Helpers


def git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """Minimal git repo with one commit, used for TaskManager and mock runner tests."""
    git(["init", "-b", "main"], tmp_path)
    git(["config", "user.email", "test@agent-graph.test"], tmp_path)
    git(["config", "user.name", "Test"], tmp_path)
    (tmp_path / "README.md").write_text("# test")
    git(["add", "."], tmp_path)
    git(["commit", "-m", "init"], tmp_path)
    return tmp_path


@pytest.fixture()
def pulsedesk_worktree(tmp_path: Path) -> Path:
    """Minimal PulseDesk-like git repo for mock runner patching tests."""
    git(["init", "-b", "main"], tmp_path)
    git(["config", "user.email", "test@agent-graph.test"], tmp_path)
    git(["config", "user.name", "Test"], tmp_path)

    # Replicate the login anchor used in the mock runner
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "__init__.py").write_text("")
    (app_dir / "main.py").write_text(
        'from fastapi import FastAPI, HTTPException, Request\n'
        'app = FastAPI()\n'
        '\n'
        '@app.post("/api/login")\n'
        'async def login(request: Request):\n'
        '        agent = get_agent_by_email(request.app.state.db_path, payload.email)\n'
        '        return {"ok": True}\n'
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_rate_limit.py").write_text("# placeholder\n")

    git(["add", "."], tmp_path)
    git(["commit", "-m", "init"], tmp_path)
    return tmp_path


# NormalizedEvent


def test_normalized_event_defaults() -> None:
    event = NormalizedEvent(type="agent_started", node_id="node-abc")
    assert event.node_id == "node-abc"
    assert event.content is None
    assert event.tool_name is None
    assert event.tool_input == {}
    assert event.is_error is False


def test_normalized_event_tool_use() -> None:
    event = NormalizedEvent(
        type="agent_tool_use",
        node_id="node-abc",
        tool_name="Read",
        tool_input={"file_path": "app/main.py"},
    )
    assert event.tool_name == "Read"
    assert event.tool_input["file_path"] == "app/main.py"


# MockAgentRunner


@pytest.mark.anyio
async def test_mock_runner_emits_started_and_completed(tmp_path: Path) -> None:
    runner = MockAgentRunner()
    events: list[NormalizedEvent] = []
    async for event in runner.stream("node-1", "Do something", str(tmp_path)):
        events.append(event)

    types = [e.type for e in events]
    assert "agent_started" in types
    assert "agent_completed" in types
    # started must be first, completed must be last
    assert types[0] == "agent_started"
    assert types[-1] == "agent_completed"


@pytest.mark.anyio
async def test_mock_runner_emits_tool_use_events(tmp_path: Path) -> None:
    runner = MockAgentRunner()
    events: list[NormalizedEvent] = []
    async for event in runner.stream("node-2", "Add rate limiting", str(tmp_path)):
        events.append(event)

    tool_events = [e for e in events if e.type == "agent_tool_use"]
    assert len(tool_events) >= 1


@pytest.mark.anyio
async def test_mock_runner_creates_file_in_non_pulsedesk_worktree(tmp_path: Path) -> None:
    """In a non-PulseDesk worktree, the mock creates a placeholder file."""
    runner = MockAgentRunner()
    async for _ in runner.stream("node-3", "Do something", str(tmp_path)):
        pass

    # Either a placeholder file or the rate_limit module was created
    files = list(tmp_path.rglob("*"))
    assert len(files) > 0  # something was written


@pytest.mark.anyio
async def test_mock_runner_patches_pulsedesk_worktree(pulsedesk_worktree: Path) -> None:
    """In a PulseDesk worktree, the mock applies the rate limiting patch."""
    runner = MockAgentRunner()
    async for _ in runner.stream("node-4", "Add rate limiting", str(pulsedesk_worktree)):
        pass

    rate_limit_py = pulsedesk_worktree / "app" / "rate_limit.py"
    assert rate_limit_py.exists(), "rate_limit.py should be created"

    main_content = (pulsedesk_worktree / "app" / "main.py").read_text()
    assert "check_rate_limit" in main_content, "login endpoint should be patched"


# _apply_rate_limiting unit tests


def test_apply_rate_limiting_patches_main_py(pulsedesk_worktree: Path) -> None:
    result = _apply_rate_limiting(str(pulsedesk_worktree))
    assert result is True

    main_content = (pulsedesk_worktree / "app" / "main.py").read_text()
    assert "check_rate_limit" in main_content
    assert "Retry-After" in main_content

    rate_limit_py = pulsedesk_worktree / "app" / "rate_limit.py"
    assert rate_limit_py.exists()


def test_apply_rate_limiting_is_idempotent(pulsedesk_worktree: Path) -> None:
    """Applying twice should not double-patch."""
    _apply_rate_limiting(str(pulsedesk_worktree))
    content_after_first = (pulsedesk_worktree / "app" / "main.py").read_text()

    _apply_rate_limiting(str(pulsedesk_worktree))
    content_after_second = (pulsedesk_worktree / "app" / "main.py").read_text()

    assert content_after_first == content_after_second


def test_apply_rate_limiting_returns_false_for_missing_main(tmp_path: Path) -> None:
    result = _apply_rate_limiting(str(tmp_path))
    assert result is False


# TaskManager


@pytest.mark.anyio
async def test_task_manager_submit_tracks_running_task() -> None:
    mgr = TaskManager()

    async def long_task() -> None:
        await asyncio.sleep(10)

    task = mgr.submit("node-x", long_task())
    assert mgr.is_running("node-x") is True
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.anyio
async def test_task_manager_cleans_up_after_completion() -> None:
    mgr = TaskManager()

    async def quick_task() -> None:
        await asyncio.sleep(0)

    task = mgr.submit("node-y", quick_task())
    await task
    # Give the done callback a chance to run
    await asyncio.sleep(0)
    assert mgr.is_running("node-y") is False


@pytest.mark.anyio
async def test_task_manager_cancel_returns_true_for_running_task() -> None:
    mgr = TaskManager()

    async def long_task() -> None:
        await asyncio.sleep(10)

    mgr.submit("node-z", long_task())
    cancelled = await mgr.cancel("node-z")
    assert cancelled is True


@pytest.mark.anyio
async def test_task_manager_cancel_returns_false_for_unknown_node() -> None:
    mgr = TaskManager()
    cancelled = await mgr.cancel("does-not-exist")
    assert cancelled is False


@pytest.mark.anyio
async def test_task_manager_running_ids_reflects_state() -> None:
    mgr = TaskManager()

    async def long_task() -> None:
        await asyncio.sleep(10)

    mgr.submit("node-a", long_task())
    mgr.submit("node-b", long_task())

    ids = mgr.running_ids()
    assert "node-a" in ids
    assert "node-b" in ids

    await mgr.cancel("node-a")
    await mgr.cancel("node-b")
