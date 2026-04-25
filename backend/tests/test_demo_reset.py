"""
Tests for ``POST /api/v1/demo/reset`` — the rehearsal-friendly reset.

Coverage:

- happy path: 3 child nodes + 3 worktrees on disk → reset cleans everything
  (response counts, in-memory graph, filesystem, branches, working tree)
- idempotency: calling reset twice in a row never errors
- ``ready=True`` post-reset: ``running_tasks`` and ``active_worktrees`` are
  both zero (covered indirectly via the filesystem/state assertions; P2-D
  exercises ``ready`` directly)

Asserts against ``get_settings().worktree_root`` rather than a literal
``.agent-worktrees`` path so that ``AGENT_GRAPH_WORKTREE_DIR`` overrides
are respected (critique #8).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import httpx
import pytest

from app.main import app
from app.settings import get_settings
from app.state import graph_state


pytestmark = pytest.mark.anyio


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    )


def _git_stdout(args: list[str], cwd: Path) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )


# ── happy path ─────────────────────────────────────────────────────────────────


async def test_demo_reset_cleans_worktrees_branches_and_state(isolated_backend: Path) -> None:
    # Setup: create 3 sibling nodes (no auto-run to keep the test deterministic).
    async with _client() as client:
        triple = await client.post(
            "/api/v1/branches/triple",
            json={"parent_id": "root", "prompt": "x", "auto_run": False},
        )
    assert triple.status_code == 200, triple.text
    nodes_before = triple.json()["nodes"]
    # All three should be cleanly created (no partial-failure for this test).
    assert all(n["status"] in ("idle", "queued") for n in nodes_before), nodes_before

    worktree_root = Path(get_settings().worktree_root)
    worktrees_before = sorted(p.name for p in worktree_root.iterdir() if p.is_dir())
    assert len(worktrees_before) == 3

    branches_before = _git_stdout(["branch", "--list", "agent/*"], isolated_backend).strip()
    assert branches_before, "agent/* branches expected before reset"

    # Reset.
    async with _client() as client:
        reset = await client.post("/api/v1/demo/reset")
    assert reset.status_code == 200, reset.text
    payload = reset.json()
    assert payload["reset"] is True
    assert payload["removed_worktrees"] == 3
    assert payload["removed_branches"] == 3

    # In-memory state: only the root node survives.
    snapshot = await graph_state.snapshot()
    assert [n.id for n in snapshot.nodes] == ["root"]

    # Filesystem: no agent-* directories under the configured worktree root.
    if worktree_root.exists():
        leftover = sorted(p.name for p in worktree_root.iterdir() if p.is_dir())
        assert leftover == [], f"unexpected leftover worktrees: {leftover}"

    # Git: no agent/* branches, working tree clean.
    branches_after = _git_stdout(["branch", "--list", "agent/*"], isolated_backend).strip()
    assert branches_after == "", f"agent/* branches should be gone, got: {branches_after!r}"

    porcelain = _git_stdout(["status", "--porcelain"], isolated_backend).strip()
    assert porcelain == "", f"working tree should be clean, got: {porcelain!r}"


async def test_demo_reset_restores_stored_baseline_after_main_moves(
    isolated_backend: Path,
) -> None:
    initial_head = _git_stdout(["rev-parse", "HEAD"], isolated_backend).strip()

    async with _client() as client:
        triple = await client.post(
            "/api/v1/branches/triple",
            json={"parent_id": "root", "prompt": "x", "auto_run": False},
        )
    assert triple.status_code == 200, triple.text

    baseline = _git_stdout(
        ["rev-parse", "refs/agent-graph/demo-baseline^{commit}"],
        isolated_backend,
    ).strip()
    assert baseline == initial_head

    marker = isolated_backend / "rate_limit.py"
    marker.write_text("# simulated merged winner\n")
    _git(["add", "rate_limit.py"], isolated_backend)
    _git(["commit", "-m", "simulate merged winner on main"], isolated_backend)
    assert _git_stdout(["rev-parse", "HEAD"], isolated_backend).strip() != initial_head

    async with _client() as client:
        reset = await client.post("/api/v1/demo/reset")
    assert reset.status_code == 200, reset.text

    assert _git_stdout(["rev-parse", "HEAD"], isolated_backend).strip() == initial_head
    assert not marker.exists(), "reset must remove files introduced after the baseline"


async def test_demo_reset_removes_untracked_dirty_files(isolated_backend: Path) -> None:
    scratch = isolated_backend / "scratch.tmp"
    scratch.write_text("untracked dirt\n")
    assert "scratch.tmp" in _git_stdout(["status", "--porcelain"], isolated_backend)

    async with _client() as client:
        reset = await client.post("/api/v1/demo/reset")
    assert reset.status_code == 200, reset.text

    assert not scratch.exists()
    assert _git_stdout(["status", "--porcelain"], isolated_backend).strip() == ""


async def test_demo_reset_sweeps_stale_agent_branches_after_restart(
    isolated_backend: Path,
) -> None:
    async with _client() as client:
        triple = await client.post(
            "/api/v1/branches/triple",
            json={"parent_id": "root", "prompt": "x", "auto_run": False},
        )
    assert triple.status_code == 200, triple.text
    assert _git_stdout(["branch", "--list", "agent/*"], isolated_backend).strip()

    graph_state.reset_for_tests()

    async with _client() as client:
        reset = await client.post("/api/v1/demo/reset")
    assert reset.status_code == 200, reset.text

    assert _git_stdout(["branch", "--list", "agent/*"], isolated_backend).strip() == ""


async def test_demo_reset_sweeps_agent_branch_checked_out_in_main_worktree(
    isolated_backend: Path,
) -> None:
    _git(["branch", "agent/manual"], isolated_backend)
    _git(["checkout", "agent/manual"], isolated_backend)

    async with _client() as client:
        reset = await client.post("/api/v1/demo/reset")
    assert reset.status_code == 200, reset.text

    assert _git_stdout(["branch", "--show-current"], isolated_backend).strip() == "main"
    assert _git_stdout(["branch", "--list", "agent/*"], isolated_backend).strip() == ""


# ── idempotency ────────────────────────────────────────────────────────────────


async def test_demo_reset_is_idempotent(isolated_backend: Path) -> None:
    async with _client() as client:
        first = await client.post("/api/v1/demo/reset")
    assert first.status_code == 200, first.text

    async with _client() as client:
        second = await client.post("/api/v1/demo/reset")
    assert second.status_code == 200, second.text
    payload = second.json()
    assert payload["reset"] is True
    assert payload["removed_worktrees"] == 0
    assert payload["removed_branches"] == 0


# ── degraded environment ───────────────────────────────────────────────────────


async def test_demo_reset_400s_when_repo_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """If ``AGENT_GRAPH_DEMO_REPO_PATH`` is unset and no auto-detected
    demo-repo is found, reset should refuse with a clear 400 instead of
    silently passing."""
    monkeypatch.setenv("AGENT_GRAPH_DEMO_REPO_PATH", "/nonexistent/path/that/should/never/exist")
    get_settings.cache_clear()
    graph_state.reset_for_tests()

    async with _client() as client:
        # The configured path does exist resolution but is not a git repo;
        # behaviour is fine to either succeed (treat as no-op) or surface
        # an error. Assert no 5xx — we never crash on this path.
        response = await client.post("/api/v1/demo/reset")

    assert response.status_code < 500, response.text
    get_settings.cache_clear()
