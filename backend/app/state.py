from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timezone

from .models import GraphEdge, GraphNode, GraphSnapshot, NodeStatus
from .settings import get_settings
from .services.worktree_service import worktree_service


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


class GraphState:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        settings = get_settings()
        root_node = GraphNode(
            id="root",
            label="Base branch",
            status="idle",
            branch_name=settings.base_branch,
            worktree_path=settings.resolved_demo_repo_path or "Set AGENT_GRAPH_DEMO_REPO_PATH",
            summary="Root node for the prepared demo repository.",
        )
        self._nodes: dict[str, GraphNode] = {root_node.id: root_node}

    async def snapshot(self) -> GraphSnapshot:
        async with self._lock:
            nodes = [deepcopy(node) for node in self._nodes.values()]
        edges = [
            GraphEdge(id=f"{node.parent_id}->{node.id}", source=node.parent_id, target=node.id)
            for node in nodes
            if node.parent_id
        ]
        settings = get_settings()
        return GraphSnapshot(
            nodes=nodes,
            edges=edges,
            base_branch=settings.base_branch,
            worktree_root=settings.worktree_root,
        )

    async def get_node(self, node_id: str) -> GraphNode | None:
        async with self._lock:
            node = self._nodes.get(node_id)
            return deepcopy(node) if node else None

    async def create_node(self, *, label: str, parent_id: str, prompt: str | None) -> GraphNode:
        async with self._lock:
            parent = self._nodes[parent_id]
            # Create the node first so we get a stable UUID-based ID
            node = GraphNode(
                label=label,
                parent_id=parent_id,
                prompt=prompt,
                branch_name="",  # filled in below
                worktree_path="",
                summary=f"Agent branch for: {prompt or label}",
            )
            # Plan the worktree using the actual node ID
            plan = worktree_service.plan_worktree(
                node_id=node.id,
                parent_branch=parent.branch_name,
            )
            node = node.model_copy(update={
                "branch_name": plan.branch_name,
                "worktree_path": plan.worktree_path,
            })
            self._nodes[node.id] = node
            return deepcopy(node)

    async def update_node_status(self, node_id: str, status: NodeStatus) -> GraphNode | None:
        async with self._lock:
            node = self._nodes.get(node_id)
            if node is None:
                return None
            updated = node.model_copy(update={"status": status, "updated_at": _utc_now()})
            self._nodes[node_id] = updated
            return deepcopy(updated)

    async def delete_node(self, node_id: str) -> GraphNode | None:
        """Remove a node and its direct children. Returns the deleted node or None."""
        async with self._lock:
            if node_id == "root" or node_id not in self._nodes:
                return None
            node = self._nodes.pop(node_id)
            # Remove direct children too
            children = [n.id for n in self._nodes.values() if n.parent_id == node_id]
            for child_id in children:
                self._nodes.pop(child_id, None)
            return deepcopy(node)


graph_state = GraphState()
