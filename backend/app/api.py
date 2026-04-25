from __future__ import annotations

import logging
import shutil
import subprocess
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import get_args

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .events import event_bus, sse_stream
from .models import (
    BranchTripleRequest,
    BranchTripleResponse,
    CreateNodeRequest,
    DeleteNodeResponse,
    DemoResetResponse,
    DemoStatusResponse,
    DiffResponse,
    GraphEvent,
    GraphNode,
    GraphSnapshot,
    HealthResponse,
    MergeResponse,
    NodeStrategy,
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


def _git(
    repo_path: Path,
    args: list[str],
    *,
    check: bool = True,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo_path),
        check=check,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _ensure_demo_baseline_ref(repo_path: Path) -> str:
    """Create the demo baseline ref once, before agent runs mutate main."""
    settings = get_settings()
    baseline_ref = settings.demo_baseline_ref
    existing = _git(
        repo_path,
        ["rev-parse", "--verify", f"{baseline_ref}^{{commit}}"],
        check=False,
    )
    if existing.returncode == 0:
        return baseline_ref

    base = _git(repo_path, ["rev-parse", f"{settings.base_branch}^{{commit}}"])
    _git(repo_path, ["update-ref", baseline_ref, base.stdout.strip()])
    return baseline_ref


def _list_agent_branches(repo_path: Path) -> list[str]:
    result = _git(
        repo_path,
        ["for-each-ref", "--format=%(refname:short)", "refs/heads/agent"],
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


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

    settings = get_settings()
    repo_path_str = settings.resolved_demo_repo_path
    if not repo_path_str:
        raise HTTPException(status_code=400, detail="Demo repo path not configured")
    try:
        _ensure_demo_baseline_ref(Path(repo_path_str))
    except subprocess.CalledProcessError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not initialize demo baseline ref: {exc.stderr.strip()}",
        ) from exc

    node = await graph_state.create_node(
        label=request.label,
        parent_id=request.parent_id,
        prompt=request.prompt,
        strategy=request.strategy,
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


@router.post("/branches/triple", response_model=BranchTripleResponse)
async def create_branch_triple(request: BranchTripleRequest) -> BranchTripleResponse:
    """Create three sibling branches from one parent — one per strategy.

    The Branch ×3 button on the frontend is the canonical caller. Each child
    is started immediately when ``auto_run=True``. Strategies map 1:1 to
    NodeStrategy and bias both the mock implementation and the Claude system
    prompt.
    """
    snapshot = await graph_state.snapshot()
    parent = next((n for n in snapshot.nodes if n.id == request.parent_id), None)
    if parent is None:
        raise HTTPException(status_code=404, detail="Parent node not found")

    settings = get_settings()
    if request.auto_run and settings.enable_real_runs and not settings.anthropic_api_key:
        raise HTTPException(
            status_code=400,
            detail="ANTHROPIC_API_KEY is not set but AGENT_GRAPH_ENABLE_REAL_RUNS=true.",
        )

    repo_path_str = settings.resolved_demo_repo_path
    if not repo_path_str:
        raise HTTPException(status_code=400, detail="Demo repo path not configured")
    try:
        _ensure_demo_baseline_ref(Path(repo_path_str))
    except subprocess.CalledProcessError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not initialize demo baseline ref: {exc.stderr.strip()}",
        ) from exc

    strategies: tuple[NodeStrategy, ...] = get_args(NodeStrategy)  # type: ignore[assignment]
    created: list[GraphNode] = []

    for index, strategy in enumerate(strategies, start=1):
        label = f"{request.label_prefix} {chr(64 + index)} — {strategy}"
        node = await graph_state.create_node(
            label=label,
            parent_id=request.parent_id,
            prompt=request.prompt,
            strategy=strategy,
        )
        try:
            worktree_service.create_worktree(
                branch_name=node.branch_name,
                worktree_path=node.worktree_path,
                parent_branch=parent.branch_name,
            )
        except WorktreeError as exc:
            logger.error("Triple-branch worktree creation failed for %s: %s", node.id, exc)
            failed_node = await graph_state.update_node_status(node.id, "failed") or node
            await event_bus.publish(
                GraphEvent(
                    type="node.created",
                    node_id=failed_node.id,
                    data={"node": failed_node.model_dump(mode="json"), "error": str(exc)},
                )
            )
            # Include failed nodes in the response so the caller sees the
            # complete attempted set; the status field communicates the outcome.
            created.append(failed_node)
            continue

        await event_bus.publish(
            GraphEvent(type="node.created", node_id=node.id, data={"node": node.model_dump(mode="json")})
        )

        if request.auto_run:
            updated = await graph_state.update_node_status(node.id, "running")
            # ``agent.started`` is emitted by the runner via task_manager —
            # see POST /run for the same single-source-of-truth note.
            task_manager.submit(
                node.id,
                run_node_task(node.id, request.prompt, node.worktree_path, strategy),
            )
            created.append(updated or node)
        else:
            created.append(node)

    return BranchTripleResponse(nodes=created)


@router.delete("/nodes/{node_id}")
async def delete_node(node_id: str) -> DeleteNodeResponse:
    node = await graph_state.get_node(node_id)
    if node is None or node_id == "root":
        raise HTTPException(status_code=404, detail="Node not found or cannot delete root")

    # Cancel any running task first
    if task_manager.is_running(node_id):
        await task_manager.cancel(node_id, reason="Cancelled by DELETE /api/v1/nodes")

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

    settings = get_settings()
    if settings.enable_real_runs and not settings.anthropic_api_key:
        raise HTTPException(
            status_code=400,
            detail=(
                "ANTHROPIC_API_KEY is not set but AGENT_GRAPH_ENABLE_REAL_RUNS=true. "
                "Either set the key or unset AGENT_GRAPH_ENABLE_REAL_RUNS."
            ),
        )

    prompt = node.prompt or "Add rate limiting to POST /api/login as described in tests/test_rate_limit.py."

    updated = await graph_state.update_node_status(node_id, "running")
    if updated is None:
        raise HTTPException(status_code=404, detail="Node not found")

    # ``agent.started`` is emitted by the runner via task_manager — single
    # source of truth for the agent lifecycle. The API only owns node-state
    # transitions and worktree CRUD events.
    task_manager.submit(node_id, run_node_task(node_id, prompt, node.worktree_path, node.strategy))

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
    repo_path_str = settings.resolved_demo_repo_path
    if not repo_path_str:
        raise HTTPException(status_code=400, detail="Demo repo path not configured")
    try:
        _ensure_demo_baseline_ref(Path(repo_path_str))
        worktree_service.merge_branch(
            branch_name=node.branch_name,
            target_branch=settings.base_branch,
        )
    except subprocess.CalledProcessError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not initialize demo baseline ref: {exc.stderr.strip()}",
        ) from exc
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


# Demo reset


@router.post("/demo/reset", response_model=DemoResetResponse)
async def demo_reset() -> DemoResetResponse:
    """Wipe all agent worktrees and branches; reset the demo repo to baseline.

    Cancels any running agent tasks, removes every worktree the backend created,
    deletes corresponding ``agent/*`` branches, runs the demo-repo reset script
    if present, and clears in-memory graph state back to the root node.
    """
    settings = get_settings()
    repo_path_str = settings.resolved_demo_repo_path
    if not repo_path_str:
        raise HTTPException(status_code=400, detail="Demo repo path not configured")
    repo_path = Path(repo_path_str)
    if not repo_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Demo repo path does not exist: {repo_path}",
        )
    if not (repo_path / ".git").exists():
        raise HTTPException(
            status_code=400,
            detail=f"Demo repo is not a git repository: {repo_path}",
        )

    try:
        baseline_ref = _ensure_demo_baseline_ref(repo_path)
    except subprocess.CalledProcessError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not initialize demo baseline ref: {exc.stderr.strip()}",
        ) from exc

    cancelled = await task_manager.cancel_all(reason="Cancelled by /api/v1/demo/reset")
    logger.info("demo.reset cancelled %d running task(s)", cancelled)

    snapshot = await graph_state.snapshot()
    removed_worktrees = 0
    removed_branches = 0
    removed_branch_names: set[str] = set()
    for node in snapshot.nodes:
        if node.id == "root":
            continue
        try:
            worktree_service.delete_worktree(
                worktree_path=node.worktree_path,
                branch_name=node.branch_name,
            )
            removed_worktrees += 1
            if node.branch_name not in removed_branch_names:
                removed_branches += 1
                removed_branch_names.add(node.branch_name)
        except WorktreeError as exc:
            logger.warning("demo.reset cleanup failed for %s: %s", node.id, exc)

    # Belt-and-braces: nuke the worktree directory and prune dangling refs.
    worktree_dir = Path(settings.worktree_root)
    if worktree_dir.exists():
        for child in worktree_dir.iterdir():
            if child.is_dir():
                try:
                    shutil.rmtree(child, ignore_errors=True)
                except Exception:  # noqa: BLE001 — best effort
                    pass
    try:
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=str(repo_path),
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        pass

    for branch_name in _list_agent_branches(repo_path):
        try:
            _git(repo_path, ["branch", "-D", branch_name])
            if branch_name not in removed_branch_names:
                removed_branches += 1
                removed_branch_names.add(branch_name)
        except subprocess.CalledProcessError as exc:
            logger.warning("demo.reset stale branch cleanup failed for %s: %s", branch_name, exc.stderr)

    # Hard-reset the demo repo to the stored hero-task baseline.
    demo_repo_reset = False
    try:
        _git(repo_path, ["checkout", settings.base_branch])
        _git(repo_path, ["reset", "--hard", baseline_ref])
        _git(repo_path, ["clean", "-fd"])
        # Re-seed the SQLite database via the demo repo's reset script
        reset_script = repo_path / "scripts" / "reset_demo.py"
        if reset_script.exists():
            try:
                subprocess.run(
                    ["uv", "run", "python", str(reset_script)],
                    cwd=str(repo_path),
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except FileNotFoundError:
                # uv missing; fall back to plain python
                subprocess.run(
                    ["python", str(reset_script)],
                    cwd=str(repo_path),
                    check=True,
                    capture_output=True,
                    text=True,
                )
        demo_repo_reset = True
    except subprocess.CalledProcessError as exc:
        logger.warning("demo.reset hard reset failed: %s", exc.stderr)

    await graph_state.reset_to_root()

    await event_bus.publish(
        GraphEvent(
            type="demo.reset",
            data={
                "removed_worktrees": removed_worktrees,
                "removed_branches": removed_branches,
                "demo_repo_reset": demo_repo_reset,
            },
        )
    )

    return DemoResetResponse(
        reset=True,
        removed_worktrees=removed_worktrees,
        removed_branches=removed_branches,
        demo_repo_reset=demo_repo_reset,
        message="Demo state reset to baseline.",
    )


@router.get("/demo/status", response_model=DemoStatusResponse)
async def demo_status() -> DemoStatusResponse:
    """One-call demo readiness probe.

    Each individual check is fail-soft (its failure adds to ``issues`` rather
    than crashing the endpoint), so this is safe to poll continuously.
    """
    settings = get_settings()
    issues: list[str] = []

    repo_path_str = settings.resolved_demo_repo_path
    repo_path = Path(repo_path_str) if repo_path_str else None

    demo_repo_exists = bool(repo_path and repo_path.exists())
    if repo_path is None:
        issues.append("Demo repo path not configured (set AGENT_GRAPH_DEMO_REPO_PATH)")
    elif not demo_repo_exists:
        issues.append(f"Demo repo path does not exist: {repo_path}")

    demo_repo_is_git = bool(repo_path and (repo_path / ".git").exists())
    if demo_repo_exists and not demo_repo_is_git:
        issues.append(f"Demo repo is not a git repository: {repo_path}")

    base_branch_clean = False
    if demo_repo_is_git and repo_path is not None:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(repo_path),
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            base_branch_clean = result.stdout.strip() == ""
            if not base_branch_clean:
                issues.append(
                    "Working tree is dirty — commit, stash, or POST /api/v1/demo/reset first"
                )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
            issues.append(f"Could not check demo repo cleanliness: {exc}")

    active_worktrees = 0
    if demo_repo_is_git and repo_path is not None:
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=str(repo_path),
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            # Each worktree entry begins with `worktree <path>`; subtract 1
            # for the main worktree (the demo repo itself).
            worktree_lines = [
                ln for ln in result.stdout.splitlines() if ln.startswith("worktree ")
            ]
            active_worktrees = max(0, len(worktree_lines) - 1)
            if active_worktrees > 0:
                issues.append(
                    f"{active_worktrees} agent worktree(s) still on disk — POST /api/v1/demo/reset to clear"
                )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
            issues.append(f"Could not enumerate worktrees: {exc}")

    api_key_present = bool(settings.anthropic_api_key and settings.anthropic_api_key.strip())
    if settings.enable_real_runs and not api_key_present:
        issues.append(
            "AGENT_GRAPH_ENABLE_REAL_RUNS=true but ANTHROPIC_API_KEY is not set"
        )

    uv_on_path = shutil.which("uv") is not None
    if settings.enable_eval and not uv_on_path:
        issues.append(
            "AGENT_GRAPH_ENABLE_EVAL=true but `uv` is not on PATH; eval will be skipped"
        )

    running = len(task_manager.running_ids())
    if running > 0:
        issues.append(f"{running} agent task(s) still running — POST /api/v1/demo/reset to cancel")

    ready = (
        demo_repo_exists
        and demo_repo_is_git
        and base_branch_clean
        and active_worktrees == 0
        and running == 0
        and (not settings.enable_real_runs or api_key_present)
        and (not settings.enable_eval or uv_on_path)
    )

    return DemoStatusResponse(
        ready=ready,
        demo_repo_path=str(repo_path) if repo_path else None,
        demo_repo_exists=demo_repo_exists,
        demo_repo_is_git=demo_repo_is_git,
        base_branch=settings.base_branch,
        base_branch_clean=base_branch_clean,
        worktree_root=settings.worktree_root,
        active_worktrees=active_worktrees,
        enable_real_runs=settings.enable_real_runs,
        anthropic_api_key_present=api_key_present,
        enable_eval=settings.enable_eval,
        uv_on_path=uv_on_path,
        running_tasks=running,
        issues=issues,
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
