from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

NodeStatus = Literal["idle", "queued", "running", "completed", "failed", "merged"]
NodeStrategy = Literal["route_local", "dependency", "middleware"]
SummaryRisk = Literal["low", "medium", "high", "unknown"]
SummaryRecommendation = Literal["merge_candidate", "needs_review", "do_not_merge"]
GraphEventType = Literal[
    # Graph lifecycle
    "graph.connected",
    "node.created",
    "node.updated",
    "node.deleted",
    "node.run_queued",
    "node.merged",
    "node.diff_ready",
    "node.eval_ready",
    "node.summary_ready",
    "demo.reset",
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


class NodeDecisionSummary(BaseModel):
    version: int = 1
    headline: str
    approach: str
    changed_files: list[str] = Field(default_factory=list)
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    tests_passed: int | None = None
    tests_failed: int | None = None
    test_summary: str | None = None
    risk: SummaryRisk = "unknown"
    risk_reason: str
    recommendation: SummaryRecommendation = "needs_review"
    review_focus: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=utc_now)


class GraphNode(BaseModel):
    id: str = Field(default_factory=lambda: f"node-{uuid4().hex[:8]}")
    label: str
    status: NodeStatus = "idle"
    branch_name: str
    worktree_path: str
    parent_id: str | None = None
    prompt: str | None = None
    summary: str | None = None
    strategy: NodeStrategy | None = None
    eval_passed: int | None = None
    eval_failed: int | None = None
    eval_summary: str | None = None
    decision_summary: NodeDecisionSummary | None = None
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
    strategy: NodeStrategy | None = None


class BranchTripleRequest(BaseModel):
    """Spawn three sibling branches from one parent, one per strategy."""

    parent_id: str
    prompt: str
    label_prefix: str = "Approach"
    auto_run: bool = True


class BranchTripleResponse(BaseModel):
    nodes: list["GraphNode"]


class DemoResetResponse(BaseModel):
    reset: bool
    removed_worktrees: int
    removed_branches: int
    demo_repo_reset: bool
    message: str


class DemoStatusResponse(BaseModel):
    """One-call answer to ‘is the backend ready for the demo?’

    ``ready`` is true only when *every* prerequisite is satisfied AND the
    backend is in a fresh state (no running tasks, no leaked worktrees).
    ``issues`` is the actionable, human-readable list of blockers — empty
    when ``ready`` is true.
    """

    ready: bool
    demo_repo_path: str | None
    demo_repo_exists: bool
    demo_repo_is_git: bool
    base_branch: str
    base_branch_clean: bool
    worktree_root: str
    active_worktrees: int
    enable_real_runs: bool
    anthropic_api_key_present: bool
    enable_eval: bool
    uv_on_path: bool
    running_tasks: int
    issues: list[str]


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


BranchTripleResponse.model_rebuild()
