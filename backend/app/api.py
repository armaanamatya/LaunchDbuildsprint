from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .events import event_bus, sse_stream
from .models import (
    CreateNodeRequest,
    DeleteNodeResponse,
    DiffResponse,
    GraphEvent,
    GraphNode,
    GraphSnapshot,
    HealthResponse,
    MergeResponse,
    RepoConfigResponse,
    RunNodeResponse,
    WorktreePlanResponse,
)
from .settings import get_settings
from .state import graph_state
from .services.repo_service import repo_service
from .services.worktree_service import MergeConflictError, WorktreeError, worktree_service
from .task_manager import run_node_task, task_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")


# Health and graph


@router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok", app="agent-graph-backend")


@router.get("/graph")
async def get_graph() -> GraphSnapshot:
    return await graph_state.snapshot()


@router.get("/repo", response_model=RepoConfigResponse)
async def get_repo_config() -> RepoConfigResponse:
    return RepoConfigResponse(**repo_service.get_repo_config().__dict__)


# Node CRUD


@router.post("/nodes")
async def create_node(request: CreateNodeRequest) -> GraphNode:
    snapshot = await graph_state.snapshot()
    parent = next((n for n in snapshot.nodes if n.id == request.parent_id), None)
    if parent is None:
        raise HTTPException(status_code=404, detail="Parent node not found")

    node = await graph_state.create_node(
        label=request.label,
        parent_id=request.parent_id,
        prompt=request.prompt,
    )

    try:
        worktree_service.create_worktree(
            branch_name=node.branch_name,
            worktree_path=node.worktree_path,
            parent_branch=parent.branch_name,
        )
    except WorktreeError as exc:
        logger.error("Worktree creation failed for node %s: %s", node.id, exc)
        node = await graph_state.update_node_status(node.id, "failed") or node
        await event_bus.publish(
            GraphEvent(type="node.created", node_id=node.id, data={"node": node.model_dump(mode="json")})
        )
        raise HTTPException(status_code=500, detail=f"Worktree creation failed: {exc}") from exc

    await event_bus.publish(
        GraphEvent(type="node.created", node_id=node.id, data={"node": node.model_dump(mode="json")})
    )
    return node


@router.delete("/nodes/{node_id}")
async def delete_node(node_id: str) -> DeleteNodeResponse:
    node = await graph_state.get_node(node_id)
    if node is None or node_id == "root":
        raise HTTPException(status_code=404, detail="Node not found or cannot delete root")

    # Cancel any running task first
    if task_manager.is_running(node_id):
        await task_manager.cancel(node_id)

    try:
        worktree_service.delete_worktree(
            worktree_path=node.worktree_path,
            branch_name=node.branch_name,
        )
    except WorktreeError as exc:
        logger.warning("Worktree cleanup failed for node %s: %s", node_id, exc)

    deleted = await graph_state.delete_node(node_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Node not found")

    await event_bus.publish(GraphEvent(type="node.deleted", node_id=node_id, data={"node_id": node_id}))
    return DeleteNodeResponse(deleted=True, node_id=node_id)


# Agent run


@router.post("/nodes/{node_id}/run", response_model=RunNodeResponse)
async def run_node(node_id: str) -> RunNodeResponse:
    """Start an agent run for a node. Returns immediately; progress streams via SSE."""
    node = await graph_state.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    if node.id == "root":
        raise HTTPException(status_code=400, detail="Cannot run the root node")
    if node.status == "running":
        raise HTTPException(status_code=409, detail="Node is already running")
    if node.status not in ("idle", "failed", "queued"):
        raise HTTPException(status_code=409, detail=f"Node cannot be run from '{node.status}' state")
    if task_manager.is_running(node_id):
        raise HTTPException(status_code=409, detail="Agent task is already active for this node")

    prompt = node.prompt or "Add rate limiting to POST /api/login as described in tests/test_rate_limit.py."

    updated = await graph_state.update_node_status(node_id, "running")
    if updated is None:
        raise HTTPException(status_code=404, detail="Node not found")

    await event_bus.publish(
        GraphEvent(
            type="agent.started",
            node_id=node_id,
            data={"prompt": prompt, "worktree_path": node.worktree_path},
        )
    )

    task_manager.submit(node_id, run_node_task(node_id, prompt, node.worktree_path))

    return RunNodeResponse(
        node_id=node_id,
        status="running",
        message="Agent started. Subscribe to /api/v1/graph/sse or /api/v1/nodes/{id}/sse for live updates.",
    )


# Diff and merge


@router.get("/nodes/{node_id}/diff", response_model=DiffResponse)
async def get_diff(node_id: str) -> DiffResponse:
    node = await graph_state.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    if node.id == "root":
        raise HTTPException(status_code=400, detail="Root node has no diff")

    settings = get_settings()
    try:
        diff_text = worktree_service.get_diff(
            base_branch=settings.base_branch,
            branch_name=node.branch_name,
        )
    except WorktreeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return DiffResponse(
        node_id=node_id,
        branch_name=node.branch_name,
        base_branch=settings.base_branch,
        diff=diff_text,
        has_changes=bool(diff_text.strip()),
    )


@router.post("/nodes/{node_id}/merge", response_model=MergeResponse)
async def merge_node(node_id: str) -> MergeResponse:
    node = await graph_state.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    if node.id == "root":
        raise HTTPException(status_code=400, detail="Cannot merge the root node")
    if node.status == "merged":
        raise HTTPException(status_code=409, detail="Node has already been merged")

    settings = get_settings()
    try:
        worktree_service.merge_branch(
            branch_name=node.branch_name,
            target_branch=settings.base_branch,
        )
    except MergeConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except WorktreeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    updated = await graph_state.update_node_status(node_id, "merged")

    await event_bus.publish(
        GraphEvent(
            type="node.merged",
            node_id=node_id,
            data={"branch_name": node.branch_name, "target_branch": settings.base_branch},
        )
    )

    return MergeResponse(
        merged=True,
        node_id=node_id,
        branch_name=node.branch_name,
        target_branch=settings.base_branch,
        message=f"Branch {node.branch_name} merged into {settings.base_branch}.",
    )


# Worktree plan utility


@router.get("/nodes/{node_id}/worktree-plan", response_model=WorktreePlanResponse)
async def get_worktree_plan(node_id: str) -> WorktreePlanResponse:
    snapshot = await graph_state.snapshot()
    node_lookup = {node.id: node for node in snapshot.nodes}
    node = node_lookup.get(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    parent_branch = snapshot.base_branch
    if node.parent_id and node.parent_id in node_lookup:
        parent_branch = node_lookup[node.parent_id].branch_name

    plan = worktree_service.plan_worktree(node_id=node.id, parent_branch=parent_branch)
    return WorktreePlanResponse(**plan.__dict__)


# SSE streams


@router.get("/graph/sse")
async def graph_sse() -> StreamingResponse:
    """Global SSE stream: all graph and agent events."""
    queue = await event_bus.subscribe()
    settings = get_settings()

    async def wrapped() -> AsyncGenerator[str, None]:
        try:
            connected = GraphEvent(
                type="graph.connected",
                data={"base_branch": settings.base_branch, "worktree_root": settings.worktree_root},
            )
            yield f"event: {connected.type}\ndata: {connected.model_dump_json()}\n\n"
            async for chunk in sse_stream(queue):
                yield chunk
        finally:
            await event_bus.unsubscribe(queue)

    return StreamingResponse(
        wrapped(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/nodes/{node_id}/sse")
async def node_sse(node_id: str) -> StreamingResponse:
    """Per-node SSE stream: filtered to events for a specific node plus heartbeats."""
    node = await graph_state.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    queue = await event_bus.subscribe()

    async def filtered() -> AsyncGenerator[str, None]:
        try:
            async for chunk in sse_stream(queue):
                # Always pass heartbeats; pass node events by checking node_id in payload
                if "heartbeat" in chunk or f'"node_id": "{node_id}"' in chunk:
                    yield chunk
        finally:
            await event_bus.unsubscribe(queue)

    return StreamingResponse(
        filtered(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
