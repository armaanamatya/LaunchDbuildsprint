export type NodeStatus =
  | "idle"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "merged";

export type GraphEventType =
  | "graph.connected"
  | "node.created"
  | "node.updated"
  | "node.deleted"
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
