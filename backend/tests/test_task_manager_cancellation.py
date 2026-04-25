"""
Tests for cancellation reason propagation through ``TaskManager`` (P2-F).

Critique #4: ``cancel()`` is called from multiple paths (``/demo/reset``,
``DELETE /nodes/{id}``). The ``agent.failed`` event must surface *which*
caller cancelled the run, not a hard-coded ``/demo/reset`` string.
"""
from __future__ import annotations

import asyncio

import pytest

from app.events import event_bus
from app.task_manager import TaskManager, run_node_task


pytestmark = pytest.mark.anyio


async def _drain_until(predicate, queue: asyncio.Queue[str], timeout: float) -> str | None:
    """Pop messages from queue until one matches predicate or timeout elapses."""
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        remaining = max(0.05, deadline - asyncio.get_event_loop().time())
        try:
            msg = await asyncio.wait_for(queue.get(), timeout=remaining)
        except asyncio.TimeoutError:
            return None
        if predicate(msg):
            return msg
    return None


async def test_cancel_propagates_reason_to_agent_failed_event(
    isolated_backend, monkeypatch
) -> None:
    """When TaskManager.cancel(reason=X) interrupts a run, the resulting
    ``agent.failed`` event must carry that reason verbatim."""
    # First create a worktree-backed node so run_node_task has somewhere to run.
    import httpx
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
        triple = await client.post(
            "/api/v1/branches/triple",
            json={"parent_id": "root", "prompt": "x", "auto_run": False},
        )
    assert triple.status_code == 200, triple.text
    node_id = triple.json()["nodes"][0]["id"]
    worktree_path = triple.json()["nodes"][0]["worktree_path"]

    # Use a long-sleeping mock-replacement so we can interrupt mid-stream.
    from app.agent_runner.base import NormalizedEvent

    class SleepyRunner:
        async def stream(self, node_id, prompt, worktree_path, strategy=None):
            yield NormalizedEvent(type="agent_started", node_id=node_id)
            await asyncio.sleep(30)  # cancelled before this completes
            yield NormalizedEvent(type="agent_completed", node_id=node_id)

    monkeypatch.setattr(
        "app.agent_runner.get_runner",
        lambda: SleepyRunner(),
    )

    mgr = TaskManager()
    queue = await event_bus.subscribe()
    try:
        mgr.submit(node_id, run_node_task(node_id, "x", worktree_path, None))
        # Let the runner emit agent_started before we cancel.
        await asyncio.sleep(0.1)
        cancelled = await mgr.cancel(node_id, reason="Cancelled by P2-F test")
        assert cancelled is True

        failed_msg = await _drain_until(
            lambda m: "event: agent.failed" in m and "P2-F test" in m,
            queue,
            timeout=2.0,
        )
        assert failed_msg is not None, "expected agent.failed event with the test reason"
        assert '"cancelled":true' in failed_msg
    finally:
        await event_bus.unsubscribe(queue)
