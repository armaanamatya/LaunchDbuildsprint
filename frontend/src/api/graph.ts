import type { GraphSnapshot } from "../types";

const FALLBACK_GRAPH: GraphSnapshot = {
  base_branch: "main",
  worktree_root: ".agent-worktrees",
  nodes: [
    {
      id: "root",
      label: "Base branch",
      status: "idle",
      branch_name: "main",
      worktree_path: "Set AGENT_GRAPH_DEMO_REPO_PATH",
      parent_id: null,
      prompt: null,
      summary: "Root node for the prepared demo repository.",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ],
  edges: [],
};

export async function fetchGraph(): Promise<GraphSnapshot> {
  try {
    const response = await fetch("/api/v1/graph");
    if (!response.ok) {
      throw new Error(`Unexpected graph status: ${response.status}`);
    }

    return (await response.json()) as GraphSnapshot;
  } catch {
    return FALLBACK_GRAPH;
  }
}
