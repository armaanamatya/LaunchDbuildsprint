"""
Tests for the per-worktree JSONL audit trail (P2-G).

The trail must:
- Land at ``<worktree>/.agent-graph/trace.jsonl``
- Be append-only, one JSON object per line
- Survive any disk error without disrupting the live agent stream
- Capture both the live event stream AND the terminal completion event
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from app.agent_runner.base import NormalizedEvent
from app.main import app
from app.models import GraphEvent
from app.services import audit_log
from app.services.audit_log import trace_path


pytestmark = pytest.mark.anyio


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    )


class _ScriptedRunner:
    """Yields a fixed event sequence — no sleeps, fully deterministic."""

    async def stream(self, node_id, prompt, worktree_path, strategy=None):
        yield NormalizedEvent(type="agent_started", node_id=node_id)
        yield NormalizedEvent(
            type="agent_text", node_id=node_id, content="working on it"
        )
        yield NormalizedEvent(
            type="agent_tool_use",
            node_id=node_id,
            tool_name="Read",
            tool_input={"file_path": "x.py"},
        )
        yield NormalizedEvent(
            type="agent_completed", node_id=node_id, content="done"
        )


async def test_run_writes_trace_jsonl_with_lifecycle_events(
    isolated_backend: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Create a worktree-backed node (auto_run=False so no concurrent task races).
    async with _client() as client:
        triple = await client.post(
            "/api/v1/branches/triple",
            json={"parent_id": "root", "prompt": "x", "auto_run": False},
        )
    assert triple.status_code == 200, triple.text
    node = triple.json()["nodes"][0]

    # Drive the run synchronously with our scripted runner — no race conditions.
    monkeypatch.setattr(
        "app.agent_runner.get_runner", lambda: _ScriptedRunner()
    )
    from app.task_manager import run_node_task

    await run_node_task(node["id"], "x", node["worktree_path"], "route_local")

    path = trace_path(node["worktree_path"])
    assert path.exists(), f"missing trace at {path}"

    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 4, f"expected ≥4 events, got {len(lines)}"

    events = [json.loads(ln) for ln in lines]
    types = [ev["type"] for ev in events]
    assert types[0] == "agent.started"
    assert "agent.text" in types
    assert "agent.tool_use" in types
    # Last lifecycle event must be a terminal one (allowing for diff_ready /
    # eval_ready being emitted after agent.completed).
    assert "agent.completed" in types
    for ev in events:
        assert "type" in ev and "timestamp" in ev


def test_audit_log_swallows_write_errors(tmp_path: Path) -> None:
    """A disk failure must NEVER raise out of audit_log.write."""
    # Point the worktree path at a child of a regular file → mkdir() will fail.
    fake_file = tmp_path / "occupied"
    fake_file.write_text("this is a regular file, not a directory")
    bad_worktree = fake_file / "wt"

    audit_log.write(
        bad_worktree,
        GraphEvent(type="agent.text", node_id="x", data={"y": 1}),
    )
    # No exception raised, no assertion needed; absence of an exception IS the contract.
