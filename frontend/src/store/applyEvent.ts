import type {
  AgentLogEntry,
  GraphEvent,
  GraphNode,
  GraphSnapshot,
  NodeStatus,
} from "../types";

export interface DiffCacheEntry {
  diff: string;
  has_changes: boolean;
}

export interface GraphState {
  graph: GraphSnapshot;
  agentLogs: Record<string, AgentLogEntry[]>;
  diffs: Record<string, DiffCacheEntry>;
}

const MAX_LOG_ENTRIES = 500;

function setNodeStatus(graph: GraphSnapshot, nodeId: string, status: NodeStatus): GraphSnapshot {
  let touched = false;
  const nodes = graph.nodes.map((n) => {
    if (n.id !== nodeId) return n;
    touched = true;
    return { ...n, status, updated_at: new Date().toISOString() };
  });
  return touched ? { ...graph, nodes } : graph;
}

function replaceNode(graph: GraphSnapshot, updated: GraphNode): GraphSnapshot {
  return {
    ...graph,
    nodes: graph.nodes.map((n) => (n.id === updated.id ? { ...n, ...updated } : n)),
  };
}

function appendLog(
  logs: Record<string, AgentLogEntry[]>,
  entry: AgentLogEntry,
): Record<string, AgentLogEntry[]> {
  const current = logs[entry.node_id] ?? [];
  const next = [...current, entry].slice(-MAX_LOG_ENTRIES);
  return { ...logs, [entry.node_id]: next };
}

function makeLogEntry(event: GraphEvent, count: number): AgentLogEntry {
  const subtype = event.type.split(".")[1] as AgentLogEntry["type"];
  return {
    id: `${event.timestamp}-${count}`,
    node_id: event.node_id ?? "",
    type: subtype,
    timestamp: event.timestamp,
    content: event.data.content as string | undefined,
    tool_name: event.data.tool_name as string | undefined,
    tool_input: event.data.tool_input as Record<string, unknown> | undefined,
    is_error: event.data.is_error as boolean | undefined,
  };
}

export function applyEvent(state: GraphState, event: GraphEvent): GraphState {
  switch (event.type) {
    case "graph.connected":
    case "heartbeat":
      return state;

    case "node.created": {
      const node = event.data.node as GraphNode | undefined;
      if (!node) return state;
      if (state.graph.nodes.some((n) => n.id === node.id)) return state;
      const edges = node.parent_id
        ? [
            ...state.graph.edges,
            { id: `${node.parent_id}->${node.id}`, source: node.parent_id, target: node.id },
          ]
        : state.graph.edges;
      return {
        ...state,
        graph: { ...state.graph, nodes: [...state.graph.nodes, node], edges },
      };
    }

    // Defensive: backend currently does NOT emit these. If future versions add
    // them with a `data.node` payload, we honor it.
    case "node.updated":
    case "node.run_queued": {
      const node = event.data.node as GraphNode | undefined;
      if (!node) return state;
      return { ...state, graph: replaceNode(state.graph, node) };
    }

    // Backend payload: {branch_name, target_branch} — no node. Use event.node_id.
    case "node.merged": {
      const id = event.node_id;
      if (!id) return state;
      return { ...state, graph: setNodeStatus(state.graph, id, "merged") };
    }

    case "node.deleted": {
      const id = event.node_id ?? (event.data.node_id as string | undefined);
      if (!id) return state;
      const { [id]: _omitLogs, ...restLogs } = state.agentLogs;
      const { [id]: _omitDiff, ...restDiffs } = state.diffs;
      return {
        ...state,
        graph: {
          ...state.graph,
          nodes: state.graph.nodes.filter((n) => n.id !== id),
          edges: state.graph.edges.filter((e) => e.source !== id && e.target !== id),
        },
        agentLogs: restLogs,
        diffs: restDiffs,
      };
    }

    // Diff payload only contains {has_changes, diff_preview}. Cache the
    // availability flag; the store action layer triggers refreshDiff for full text.
    case "node.diff_ready": {
      const id = event.node_id;
      if (!id) return state;
      const has_changes = Boolean(event.data.has_changes);
      return { ...state, diffs: { ...state.diffs, [id]: { diff: "", has_changes } } };
    }

    // Status inference: backend updates server-side state but does not broadcast
    // a node.updated. We derive status from the agent lifecycle.
    case "agent.started": {
      const id = event.node_id;
      if (!id) return state;
      return {
        ...state,
        graph: setNodeStatus(state.graph, id, "running"),
        agentLogs: appendLog(state.agentLogs, makeLogEntry(event, state.agentLogs[id]?.length ?? 0)),
      };
    }

    case "agent.completed": {
      const id = event.node_id;
      if (!id) return state;
      return {
        ...state,
        graph: setNodeStatus(state.graph, id, "completed"),
        agentLogs: appendLog(state.agentLogs, makeLogEntry(event, state.agentLogs[id]?.length ?? 0)),
      };
    }

    case "agent.failed": {
      const id = event.node_id;
      if (!id) return state;
      return {
        ...state,
        graph: setNodeStatus(state.graph, id, "failed"),
        agentLogs: appendLog(state.agentLogs, makeLogEntry(event, state.agentLogs[id]?.length ?? 0)),
      };
    }

    case "agent.text":
    case "agent.tool_use":
    case "agent.tool_result": {
      const id = event.node_id;
      if (!id) return state;
      return {
        ...state,
        agentLogs: appendLog(state.agentLogs, makeLogEntry(event, state.agentLogs[id]?.length ?? 0)),
      };
    }

    // stored on the node so compare panel reads it without a refetch
    case "node.eval_ready": {
      const id = event.node_id;
      if (!id) return state;
      const data = event.data ?? {};
      const passed = typeof data.passed === "number" ? data.passed : null;
      const failed = typeof data.failed === "number" ? data.failed : null;
      const summary = typeof data.summary === "string" ? data.summary : null;
      return {
        ...state,
        graph: {
          ...state.graph,
          nodes: state.graph.nodes.map((n) =>
            n.id === id
              ? { ...n, eval_passed: passed, eval_failed: failed, eval_summary: summary }
              : n,
          ),
        },
      };
    }

    // keeps state consistent if the SSE event arrives before resetDemo's response
    case "demo.reset": {
      const root = state.graph.nodes.find((n) => n.parent_id === null);
      return {
        ...state,
        graph: {
          ...state.graph,
          nodes: root ? [root] : [],
          edges: [],
        },
        agentLogs: {},
        diffs: {},
      };
    }

    default: {
      const _exhaustive: never = event.type;
      void _exhaustive;
      return state;
    }
  }
}
