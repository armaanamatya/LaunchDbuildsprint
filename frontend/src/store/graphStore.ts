import { create } from "zustand";
import { fetchGraph } from "../api/graph";
import type { GraphSnapshot, GraphNode } from "../types";

type GraphStore = {
  graph: GraphSnapshot;
  selectedNodeId: string;
  isLoading: boolean;
  loadGraph: () => Promise<void>;
  selectNode: (nodeId: string) => void;
  addDraftBranch: () => void;
};

const now = () => new Date().toISOString();

const initialGraph: GraphSnapshot = {
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
      created_at: now(),
      updated_at: now(),
    },
  ],
  edges: [],
};

export const useGraphStore = create<GraphStore>((set, get) => ({
  graph: initialGraph,
  selectedNodeId: "root",
  isLoading: false,
  loadGraph: async () => {
    set({ isLoading: true });
    const graph = await fetchGraph();
    set({
      graph,
      selectedNodeId: graph.nodes[0]?.id ?? "root",
      isLoading: false,
    });
  },
  selectNode: (nodeId) => set({ selectedNodeId: nodeId }),
  addDraftBranch: () => {
    const graph = get().graph;
    const root = graph.nodes.find((node) => node.id === "root") ?? graph.nodes[0];
    const nextIndex = graph.nodes.length;
    const node: GraphNode = {
      id: `draft-${nextIndex}`,
      label: `Approach ${nextIndex}`,
      status: "queued",
      branch_name: `${graph.base_branch}-agent-${nextIndex}`,
      worktree_path: `${graph.worktree_root}/${graph.base_branch}-agent-${nextIndex}`,
      parent_id: root.id,
      prompt: "Implement the hero task with a different approach.",
      summary: "Draft branch created from the frontend shell.",
      created_at: now(),
      updated_at: now(),
    };
    set({
      graph: {
        ...graph,
        nodes: [...graph.nodes, node],
        edges: [
          ...graph.edges,
          {
            id: `${root.id}->${node.id}`,
            source: root.id,
            target: node.id,
          },
        ],
      },
      selectedNodeId: node.id,
    });
  },
}));
