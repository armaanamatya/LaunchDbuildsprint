"""
Tests for ``POST /api/v1/branches/triple`` — the demo-day Branch ×3 endpoint.

Coverage:

- happy path with ``auto_run=False``: 3 sibling nodes created, one per
  strategy, branch names follow the ``agent/`` namespace convention
- ``auto_run=True``: each node transitions to ``running`` and an
  ``agent.started`` event is published per strategy
- 404 when ``parent_id`` does not exist
- ``auto_run=False`` succeeds even when ``ANTHROPIC_API_KEY`` is missing and
  ``AGENT_GRAPH_ENABLE_REAL_RUNS=true`` (preflight only fires on auto_run)
- ``auto_run=True`` 400s when the API key is missing and real runs are on
- partial-failure resilience: if one of three ``create_worktree`` calls
  raises, the response still contains all three nodes with the failing one
  marked ``failed`` and the surviving ones still ``running``/``idle``
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest

from app.events import event_bus
from app.main import app
from app.services.worktree_service import WorktreeError, worktree_service


pytestmark = pytest.mark.anyio


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    )


async def _drain_events(timeout: float, predicate) -> list[str]:
    """Subscribe to event_bus, collect SSE message strings matching predicate
    until timeout. Returns the list (possibly empty)."""
    queue = await event_bus.subscribe()
    messages: list[str] = []
    try:
        loop_deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < loop_deadline:
            try:
                msg = await asyncio.wait_for(
                    queue.get(), timeout=max(0.05, loop_deadline - asyncio.get_event_loop().time())
                )
            except asyncio.TimeoutError:
                break
            if predicate(msg):
                messages.append(msg)
        return messages
    finally:
        await event_bus.unsubscribe(queue)


# ── happy paths ────────────────────────────────────────────────────────────────


async def test_branch_triple_creates_three_strategy_siblings(isolated_backend: Path) -> None:
    async with _client() as client:
        response = await client.post(
            "/api/v1/branches/triple",
            json={
                "parent_id": "root",
                "prompt": "Add rate limiting to POST /api/login",
                "auto_run": False,
            },
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    nodes = payload["nodes"]
    assert len(nodes) == 3

    strategies = {n["strategy"] for n in nodes}
    assert strategies == {"route_local", "dependency", "middleware"}

    for node in nodes:
        assert node["parent_id"] == "root"
        assert node["branch_name"].startswith("agent/")
        assert node["worktree_path"].startswith(str(isolated_backend))
        # auto_run=False keeps nodes idle (worktree was created on disk only)
        assert node["status"] in ("idle", "queued")


async def test_branch_triple_auto_run_publishes_three_agent_started_events(
    isolated_backend: Path,
) -> None:
    drain = asyncio.create_task(
        _drain_events(timeout=3.0, predicate=lambda m: "event: agent.started" in m)
    )
    # Yield so the subscriber registers before the API call publishes events.
    await asyncio.sleep(0.05)

    async with _client() as client:
        response = await client.post(
            "/api/v1/branches/triple",
            json={
                "parent_id": "root",
                "prompt": "Add rate limiting to POST /api/login",
                "auto_run": True,
            },
        )

    assert response.status_code == 200, response.text
    nodes = response.json()["nodes"]
    assert len(nodes) == 3
    for node in nodes:
        assert node["status"] == "running"

    started_msgs = await drain
    assert len(started_msgs) == 3, f"expected 3 agent.started events, got {len(started_msgs)}"


# ── negative paths ─────────────────────────────────────────────────────────────


async def test_branch_triple_rejects_unknown_parent(isolated_backend: Path) -> None:
    async with _client() as client:
        response = await client.post(
            "/api/v1/branches/triple",
            json={"parent_id": "does-not-exist", "prompt": "x", "auto_run": False},
        )
    assert response.status_code == 404


async def test_branch_triple_no_run_succeeds_without_api_key(
    isolated_backend: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """auto_run=False must NOT preflight the API key — caller may run later."""
    monkeypatch.setenv("AGENT_GRAPH_ENABLE_REAL_RUNS", "true")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from app.settings import get_settings

    get_settings.cache_clear()

    async with _client() as client:
        response = await client.post(
            "/api/v1/branches/triple",
            json={"parent_id": "root", "prompt": "x", "auto_run": False},
        )

    assert response.status_code == 200, response.text
    assert len(response.json()["nodes"]) == 3


async def test_branch_triple_auto_run_400s_without_api_key(
    isolated_backend: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AGENT_GRAPH_ENABLE_REAL_RUNS", "true")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from app.settings import get_settings

    get_settings.cache_clear()

    async with _client() as client:
        response = await client.post(
            "/api/v1/branches/triple",
            json={"parent_id": "root", "prompt": "x", "auto_run": True},
        )

    assert response.status_code == 400
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]


# ── partial-failure resilience (critique #7) ───────────────────────────────────


async def test_branch_triple_partial_worktree_failure_still_returns_all_three(
    isolated_backend: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If one create_worktree raises, the response includes all three nodes,
    the failing one as status=failed, the others as idle/running."""
    real_create = worktree_service.create_worktree
    call_count = {"n": 0}

    def flaky_create(branch_name, worktree_path, parent_branch, repo_path=None):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise WorktreeError("simulated worktree failure")
        return real_create(
            branch_name=branch_name,
            worktree_path=worktree_path,
            parent_branch=parent_branch,
            repo_path=repo_path,
        )

    monkeypatch.setattr(worktree_service, "create_worktree", flaky_create)

    async with _client() as client:
        response = await client.post(
            "/api/v1/branches/triple",
            json={"parent_id": "root", "prompt": "x", "auto_run": False},
        )

    assert response.status_code == 200, response.text
    nodes = response.json()["nodes"]
    assert len(nodes) == 3, "all three attempts must appear in the response"

    statuses = [n["status"] for n in nodes]
    assert statuses.count("failed") == 1
    assert statuses.count("idle") == 2
