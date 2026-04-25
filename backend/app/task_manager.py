"""
Task manager: tracks background agent runs per node.
Provides run_node_task, the async coroutine that drives a full agent run.
"""
from __future__ import annotations

import asyncio
import logging

from .events import event_bus
from .models import GraphEvent, GraphEventType
from .state import graph_state
from .services.worktree_service import worktree_service
from .settings import get_settings

logger = logging.getLogger(__name__)

# Map NormalizedEvent.type to GraphEventType.
_NORMALIZED_TO_GRAPH: dict[str, GraphEventType] = {
    "agent_started": "agent.started",
    "agent_text": "agent.text",
    "agent_tool_use": "agent.tool_use",
    "agent_tool_result": "agent.tool_result",
    "agent_completed": "agent.completed",
    "agent_failed": "agent.failed",
}


class TaskManager:
    """Registry of active background agent-run tasks."""

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def submit(self, node_id: str, coro: object) -> asyncio.Task[None]:
        """Submit a coroutine as a background asyncio task for *node_id*."""
        task: asyncio.Task[None] = asyncio.create_task(coro, name=f"agent-run-{node_id}")  # type: ignore[arg-type]
        self._tasks[node_id] = task
        task.add_done_callback(lambda _: self._tasks.pop(node_id, None))
        return task

    def is_running(self, node_id: str) -> bool:
        task = self._tasks.get(node_id)
        return task is not None and not task.done()

    def running_ids(self) -> list[str]:
        return [nid for nid, t in self._tasks.items() if not t.done()]

    async def cancel(self, node_id: str) -> bool:
        task = self._tasks.get(node_id)
        if task is None or task.done():
            return False
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass
        return True


task_manager = TaskManager()


async def run_node_task(node_id: str, prompt: str, worktree_path: str) -> None:
    """Background coroutine: drives the agent, publishes events, updates node status."""
    from .agent_runner import get_runner

    settings = get_settings()
    runner = get_runner()

    try:
        async for event in runner.stream(node_id, prompt, worktree_path):
            graph_event_type = _NORMALIZED_TO_GRAPH.get(event.type, "agent.text")
            graph_event = GraphEvent(
                type=graph_event_type,
                node_id=node_id,
                data={
                    k: v
                    for k, v in {
                        "content": event.content,
                        "tool_name": event.tool_name,
                        "tool_input": event.tool_input or {},
                        "is_error": event.is_error,
                    }.items()
                    if v is not None and v != {} and v is not False
                },
            )
            await event_bus.publish(graph_event)

            if event.type == "agent_completed":
                await graph_state.update_node_status(node_id, "completed")
                # Publish diff_ready so the frontend knows to fetch the diff
                try:
                    node = await graph_state.get_node(node_id)
                    if node:
                        diff = worktree_service.get_diff(settings.base_branch, node.branch_name)
                        await event_bus.publish(
                            GraphEvent(
                                type="node.diff_ready",
                                node_id=node_id,
                                data={
                                    "has_changes": bool(diff.strip()),
                                    "diff_preview": diff[:400] if diff.strip() else "",
                                },
                            )
                        )
                except Exception as diff_exc:
                    logger.warning("Could not compute diff for node %s after completion: %s", node_id, diff_exc)

            elif event.type == "agent_failed":
                await graph_state.update_node_status(node_id, "failed")

    except asyncio.CancelledError:
        logger.info("Run task cancelled for node %s", node_id)
        await graph_state.update_node_status(node_id, "failed")
        raise

    except Exception as exc:
        logger.error("run_node_task unhandled error for node %s: %s", node_id, exc, exc_info=True)
        await graph_state.update_node_status(node_id, "failed")
        await event_bus.publish(
            GraphEvent(
                type="agent.failed",
                node_id=node_id,
                data={"error": str(exc)},
            )
        )
