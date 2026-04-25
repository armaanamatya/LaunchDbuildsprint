import { create } from "zustand";
import {
  ApiError,
  createNode as apiCreateNode,
  deleteNode as apiDeleteNode,
  fetchDiff as apiFetchDiff,
  fetchGraph,
  mergeBranch as apiMergeBranch,
  runNode as apiRunNode,
} from "../api/graph";
import { applyEvent, type GraphState } from "./applyEvent";
import type { GraphEvent, GraphNode, GraphSnapshot } from "../types";

export type ConnectionStatus = "connecting" | "open" | "reconnecting" | "closed";

export type Toast = {
  id: string;
  kind: "info" | "success" | "error";
  message: string;
};

export type CompareMode = { open: boolean; nodeIds: string[] };

type Store = GraphState & {
  selectedNodeId: string;
  isLoading: boolean;
  loadError: string | null;
  connection: ConnectionStatus;
  compare: CompareMode;
  toasts: Toast[];
  // selectors / mutators
  loadGraph: () => Promise<void>;
  selectNode: (nodeId: string) => void;
  setConnection: (s: ConnectionStatus) => void;
  ingest: (event: GraphEvent) => void;
  // async actions
  createBranch: (label: string, prompt: string) => Promise<GraphNode | null>;
  runBranch: (nodeId: string) => Promise<void>;
  deleteBranch: (nodeId: string) => Promise<void>;
  mergeBranch: (nodeId: string) => Promise<void>;
  refreshDiff: (nodeId: string) => Promise<void>;
  resetDemo: () => Promise<void>;
  // compare-mode
  toggleCompareNode: (nodeId: string) => void;
  openCompare: () => void;
  closeCompare: () => void;
  // toasts
  pushToast: (kind: Toast["kind"], message: string) => void;
  dismissToast: (id: string) => void;
};

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
      strategy: null,
      eval_passed: null,
      eval_failed: null,
      eval_summary: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ],
  edges: [],
};

let toastSeq = 0;

export const useGraphStore = create<Store>((set, get) => ({
  graph: initialGraph,
  agentLogs: {},
  diffs: {},
  selectedNodeId: "root",
  isLoading: false,
  loadError: null,
  connection: "connecting",
  compare: { open: false, nodeIds: [] },
  toasts: [],

  loadGraph: async () => {
    set({ isLoading: true, loadError: null });
    try {
      const graph = await fetchGraph();
      set({
        graph,
        selectedNodeId: graph.nodes[0]?.id ?? "root",
        isLoading: false,
      });
    } catch (err) {
      set({
        isLoading: false,
        loadError: err instanceof Error ? err.message : "Failed to load graph",
      });
      get().pushToast("error", "Could not load graph from backend.");
    }
  },

  selectNode: (nodeId) => set({ selectedNodeId: nodeId }),

  setConnection: (connection) => set({ connection }),

  ingest: (event) => {
    set((s) => applyEvent(
      { graph: s.graph, agentLogs: s.agentLogs, diffs: s.diffs },
      event,
    ));
    // Side-effect: backend's node.diff_ready only carries a flag; fetch full diff.
    if (event.type === "node.diff_ready" && event.node_id) {
      void get().refreshDiff(event.node_id);
    }
  },

  createBranch: async (label, prompt) => {
    const root = get().graph.nodes.find((n) => n.parent_id === null);
    if (!root) {
      get().pushToast("error", "No root node — cannot create branch.");
      return null;
    }
    try {
      const node = await apiCreateNode({
        label,
        parent_id: root.id,
        prompt: prompt || null,
      });
      // Optimistic insert; SSE node.created will be ignored as duplicate.
      set((s) => ({
        graph: {
          ...s.graph,
          nodes: s.graph.nodes.some((n) => n.id === node.id)
            ? s.graph.nodes
            : [...s.graph.nodes, node],
          edges: s.graph.edges.some((e) => e.target === node.id)
            ? s.graph.edges
            : [
                ...s.graph.edges,
                { id: `${root.id}->${node.id}`, source: root.id, target: node.id },
              ],
        },
        selectedNodeId: node.id,
      }));
      get().pushToast("success", `Branch ${node.branch_name} created.`);
      return node;
    } catch (err) {
      get().pushToast("error", apiErrorMessage(err, "Could not create branch"));
      return null;
    }
  },

  runBranch: async (nodeId) => {
    try {
      await apiRunNode(nodeId);
      get().pushToast("info", "Agent run queued.");
    } catch (err) {
      get().pushToast("error", apiErrorMessage(err, "Could not start agent"));
    }
  },

  deleteBranch: async (nodeId) => {
    if (nodeId === "root") return;
    try {
      await apiDeleteNode(nodeId);
      // SSE node.deleted will reconcile state.
    } catch (err) {
      get().pushToast("error", apiErrorMessage(err, "Could not delete branch"));
    }
  },

  mergeBranch: async (nodeId) => {
    try {
      const result = await apiMergeBranch(nodeId);
      get().pushToast("success", result.message || "Merged.");
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        get().pushToast("error", "Merge conflict — resolve manually then retry.");
      } else {
        get().pushToast("error", apiErrorMessage(err, "Merge failed"));
      }
    }
  },

  refreshDiff: async (nodeId) => {
    try {
      const result = await apiFetchDiff(nodeId);
      set((s) => ({
        diffs: { ...s.diffs, [nodeId]: { diff: result.diff, has_changes: result.has_changes } },
      }));
    } catch (err) {
      get().pushToast("error", apiErrorMessage(err, "Could not load diff"));
    }
  },

  resetDemo: async () => {
    const nonRoot = get().graph.nodes.filter((n) => n.parent_id !== null);
    for (const node of nonRoot) {
      try {
        await apiDeleteNode(node.id);
      } catch {
        /* ignore — UI will reconcile from SSE */
      }
    }
    get().pushToast("info", "Demo reset.");
  },

  toggleCompareNode: (nodeId) => {
    set((s) => {
      const isIn = s.compare.nodeIds.includes(nodeId);
      const nodeIds = isIn
        ? s.compare.nodeIds.filter((id) => id !== nodeId)
        : [...s.compare.nodeIds, nodeId].slice(-3);
      return { compare: { ...s.compare, nodeIds } };
    });
  },
  openCompare: () => set((s) => ({ compare: { ...s.compare, open: true } })),
  closeCompare: () => set((s) => ({ compare: { ...s.compare, open: false } })),

  pushToast: (kind, message) => {
    const id = `t-${++toastSeq}`;
    set((s) => ({ toasts: [...s.toasts, { id, kind, message }] }));
    setTimeout(() => get().dismissToast(id), 4000);
  },
  dismissToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

function apiErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof ApiError) return `${fallback}: ${err.message}`;
  if (err instanceof Error) return `${fallback}: ${err.message}`;
  return fallback;
}

