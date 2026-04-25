"""
Task manager: tracks background agent runs per node.
Provides run_node_task, the async coroutine that drives a full agent run.
"""
from __future__ import annotations

import asyncio
import logging
import re
import subprocess

from .events import event_bus
from .models import GraphEvent, GraphEventType, NodeStrategy
from .state import graph_state
from .services import audit_log
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

    async def cancel(self, node_id: str, reason: str | None = None) -> bool:
        """Cancel the running task for ``node_id``.

        ``reason`` is propagated to the task's ``CancelledError`` so the
        agent run can publish a structured ``agent.failed`` event explaining
        *why* it stopped — useful when distinguishing /demo/reset from
        DELETE /nodes/{id} from a manual stop.
        """
        task = self._tasks.get(node_id)
        if task is None or task.done():
            return False
        task.cancel(msg=reason or "Run cancelled")
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass
        return True

    async def cancel_all(self, reason: str | None = None) -> int:
        ids = list(self._tasks.keys())
        cancelled = 0
        for node_id in ids:
            if await self.cancel(node_id, reason=reason):
                cancelled += 1
        return cancelled

    def reset_for_tests(self) -> None:
        """Drop all task references without awaiting cancellation. Test-only."""
        self._tasks.clear()


task_manager = TaskManager()


# Pytest summary regex (e.g. "4 passed, 0 failed in 1.23s" or "1 failed, 5 passed").
_PYTEST_SUMMARY_RE = re.compile(
    r"(?:(?P<passed>\d+)\s+passed)|(?:(?P<failed>\d+)\s+failed)",
    re.IGNORECASE,
)


def _parse_pytest_summary(output: str) -> tuple[int, int]:
    passed = 0
    failed = 0
    for match in _PYTEST_SUMMARY_RE.finditer(output):
        if match.group("passed"):
            passed = max(passed, int(match.group("passed")))
        if match.group("failed"):
            failed = max(failed, int(match.group("failed")))
    return passed, failed


async def _emit_eval(node_id: str, worktree_path: str, event: GraphEvent) -> None:
    """Publish + audit-log helper for eval events (mirrors run_node_task._emit)."""
    await event_bus.publish(event)
    audit_log.write(worktree_path, event)


async def _run_eval(node_id: str, worktree_path: str) -> None:
    """Run the rate-limit acceptance tests inside the worktree and publish a result event."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "uv",
            "run",
            "pytest",
            "tests/test_rate_limit.py",
            "-q",
            "--no-header",
            cwd=worktree_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            await _emit_eval(
                node_id,
                worktree_path,
                GraphEvent(
                    type="node.eval_ready",
                    node_id=node_id,
                    data={"passed": 0, "failed": 0, "summary": "Eval timed out after 120s"},
                ),
            )
            return

        output = stdout.decode("utf-8", errors="replace") if stdout else ""
        passed, failed = _parse_pytest_summary(output)
        summary = f"{passed} passed, {failed} failed" if (passed or failed) else "no tests collected"

        await graph_state.update_node_fields(
            node_id,
            eval_passed=passed,
            eval_failed=failed,
            eval_summary=summary,
        )
        await _emit_eval(
            node_id,
            worktree_path,
            GraphEvent(
                type="node.eval_ready",
                node_id=node_id,
                data={"passed": passed, "failed": failed, "summary": summary},
            ),
        )

    except FileNotFoundError:
        # `uv` not on PATH — eval is best-effort, not critical for the demo loop.
        logger.warning("uv not on PATH; skipping eval for node %s", node_id)
    except Exception as exc:
        logger.warning("Eval failed for node %s: %s", node_id, exc)


async def run_node_task(
    node_id: str,
    prompt: str,
    worktree_path: str,
    strategy: NodeStrategy | None = None,
) -> None:
    """Background coroutine: drives the agent, publishes events, updates node status.

    Wrapped in a wall-clock budget (``AGENT_GRAPH_MAX_RUN_SECONDS``). When the
    budget is exhausted the inner stream is cancelled — the cancellation
    handler still publishes ``agent.failed`` and marks the node failed, but
    we tag the event with ``timed_out: True`` so the UI can phrase the
    failure precisely instead of saying "cancelled".
    """
    from .agent_runner import get_runner

    settings = get_settings()
    runner = get_runner()
    timeout_seconds = max(30, settings.max_run_seconds)

    async def _emit(graph_event: GraphEvent) -> None:
        """Publish to live SSE subscribers and append to the per-node trace.

        Audit-log failures are swallowed inside ``audit_log.write`` so a
        broken trace file can never disrupt the live stream.
        """
        await event_bus.publish(graph_event)
        audit_log.write(worktree_path, graph_event)

    async def _drive() -> None:
        async for event in runner.stream(node_id, prompt, worktree_path, strategy):
            graph_event_type = _NORMALIZED_TO_GRAPH.get(event.type, "agent.text")
            data = {
                k: v
                for k, v in {
                    "content": event.content,
                    "tool_name": event.tool_name,
                    "tool_input": event.tool_input or {},
                    "is_error": event.is_error,
                }.items()
                if v is not None and v != {} and v is not False
            }
            # Single source of truth for ``agent.started``: enrich it here
            # with the run context (prompt / worktree / strategy) so the API
            # endpoints don't have to emit a duplicate event of their own.
            if event.type == "agent_started":
                data.update(
                    {
                        "prompt": prompt,
                        "worktree_path": worktree_path,
                        "strategy": strategy,
                    }
                )
            await _emit(GraphEvent(type=graph_event_type, node_id=node_id, data=data))

            if event.type == "agent_completed":
                await graph_state.update_node_status(node_id, "completed")
                # Publish diff_ready so the frontend knows to fetch the diff,
                # plus a fingerprint so the UI can render a "X files / +Y -Z"
                # tag without re-fetching the full patch text.
                try:
                    node = await graph_state.get_node(node_id)
                    if node:
                        diff = worktree_service.get_diff(settings.base_branch, node.branch_name)
                        summary = worktree_service.get_diff_summary(
                            settings.base_branch, node.branch_name
                        )
                        await _emit(
                            GraphEvent(
                                type="node.diff_ready",
                                node_id=node_id,
                                data={
                                    "has_changes": bool(diff.strip()),
                                    "diff_preview": diff[:400] if diff.strip() else "",
                                    "files_changed": summary.files_changed,
                                    "insertions": summary.insertions,
                                    "deletions": summary.deletions,
                                },
                            )
                        )
                except Exception as diff_exc:
                    logger.warning("diff_unavailable node=%s reason=%s", node_id, diff_exc)

                # Best-effort eval — runs in the same task so completion is observable.
                if settings.enable_eval:
                    try:
                        await _run_eval(node_id, worktree_path)
                    except Exception as eval_exc:
                        logger.warning("eval_skipped node=%s reason=%s", node_id, eval_exc)

            elif event.type == "agent_failed":
                await graph_state.update_node_status(node_id, "failed")

    try:
        await asyncio.wait_for(_drive(), timeout=timeout_seconds)

    except asyncio.TimeoutError:
        logger.warning("agent_timeout node=%s after=%ss", node_id, timeout_seconds)
        await graph_state.update_node_status(node_id, "failed")
        await _emit(
            GraphEvent(
                type="agent.failed",
                node_id=node_id,
                data={
                    "error": f"Agent run exceeded {timeout_seconds}s and was cancelled.",
                    "timed_out": True,
                },
            )
        )

    except asyncio.CancelledError as exc:
        reason = (str(exc) if exc.args else "") or "Run cancelled"
        logger.info("agent_cancelled node=%s reason=%s", node_id, reason)
        await graph_state.update_node_status(node_id, "failed")
        await _emit(
            GraphEvent(
                type="agent.failed",
                node_id=node_id,
                data={"error": reason, "cancelled": True},
            )
        )
        raise

    except Exception as exc:
        logger.error("agent_unhandled_error node=%s err=%s", node_id, exc, exc_info=True)
        await graph_state.update_node_status(node_id, "failed")
        await _emit(
            GraphEvent(
                type="agent.failed",
                node_id=node_id,
                data={"error": str(exc)},
            )
        )
