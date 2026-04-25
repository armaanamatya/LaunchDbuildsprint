from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

NodeStatus = Literal["idle", "queued", "running", "completed", "failed", "merged"]
GraphEventType = Literal[
    # Graph lifecycle
    "graph.connected",
    "node.created",
    "node.updated",
    "node.deleted",
    "node.run_queued",
    "node.merged",
    "node.diff_ready",
    # Agent lifecycle
    "agent.started",
    "agent.text",
    "agent.tool_use",
    "agent.tool_result",
    "agent.completed",
    "agent.failed",
    # Connection
    "heartbeat",
]


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


class GraphNode(BaseModel):
    id: str = Field(default_factory=lambda: f"node-{uuid4().hex[:8]}")
    label: str
    status: NodeStatus = "idle"
    branch_name: str
    worktree_path: str
    parent_id: str | None = None
    prompt: str | None = None
    summary: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str


class GraphSnapshot(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    base_branch: str
    worktree_root: str


class GraphEvent(BaseModel):
    type: GraphEventType
    timestamp: datetime = Field(default_factory=utc_now)
    node_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    app: str


class CreateNodeRequest(BaseModel):
    label: str
    parent_id: str
    prompt: str | None = None


class DeleteNodeResponse(BaseModel):
    deleted: bool
    node_id: str


class RepoConfigResponse(BaseModel):
    repo_path: str | None
    repo_exists: bool
    git_dir_exists: bool
    base_branch: str
    worktree_root: str
    worktree_root_exists: bool


class WorktreePlanResponse(BaseModel):
    node_id: str
    parent_branch: str
    branch_name: str
    worktree_path: str
    implemented: bool = False


class DiffResponse(BaseModel):
    node_id: str
    branch_name: str
    base_branch: str
    diff: str
    has_changes: bool


class MergeResponse(BaseModel):
    merged: bool
    node_id: str
    branch_name: str
    target_branch: str
    message: str


class RunNodeResponse(BaseModel):
    node_id: str
    status: NodeStatus
    message: str
