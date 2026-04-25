export type NodeStatus =
  | "idle"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "merged";

export type NodeStrategy = "route_local" | "dependency" | "middleware";

export type GraphEventType =
  | "graph.connected"
  | "node.created"
  | "node.updated"
  | "node.deleted"
  | "node.run_queued"
  | "node.merged"
  | "node.diff_ready"
  | "node.eval_ready"
  | "demo.reset"
  | "agent.started"
  | "agent.text"
  | "agent.tool_use"
  | "agent.tool_result"
  | "agent.completed"
  | "agent.failed"
  | "heartbeat";

export interface GraphNode extends Record<string, unknown> {
  id: string;
  label: string;
  status: NodeStatus;
  branch_name: string;
  worktree_path: string;
  parent_id: string | null;
  prompt: string | null;
  summary: string | null;
  strategy: NodeStrategy | null;
  eval_passed: number | null;
  eval_failed: number | null;
  eval_summary: string | null;
  created_at: string;
  updated_at: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
}

export interface GraphSnapshot {
  nodes: GraphNode[];
  edges: GraphEdge[];
  base_branch: string;
  worktree_root: string;
}

export interface GraphEvent extends Record<string, unknown> {
  type: GraphEventType;
  timestamp: string;
  node_id: string | null;
  data: Record<string, unknown>;
}

export interface DiffResponse {
  node_id: string;
  branch_name: string;
  base_branch: string;
  diff: string;
  has_changes: boolean;
}

export interface MergeResponse {
  merged: boolean;
  node_id: string;
  branch_name: string;
  target_branch: string;
  message: string;
}

export interface BranchTripleResponse {
  nodes: GraphNode[];
}

export interface DemoResetResponse {
  reset: boolean;
  removed_worktrees: number;
  removed_branches: number;
  demo_repo_reset: boolean;
  message: string;
}

export interface AgentLogEntry {
  id: string;
  kind: "started" | "text" | "tool_use" | "tool_result" | "completed" | "failed";
  text: string;
  tool_name?: string;
  tool_input?: Record<string, unknown>;
  is_error?: boolean;
  timestamp: string;
}

export interface NodeEvalResult {
  passed: number;
  failed: number;
  summary: string;
}
