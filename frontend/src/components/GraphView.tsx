import {
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  type Edge,
  type Node as RfNode,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import dagre from "dagre";
import { useMemo } from "react";
import type { GraphNode, GraphSnapshot, NodeStatus } from "../types";
import { AnimatedEdge } from "./edges/AnimatedEdge";
import { WorktreeNode, type WorktreeFlowNode } from "./WorktreeNode";

function statusColor(status: NodeStatus): string {
  switch (status) {
    case "running":
    case "queued":
      return "#d8492e"; // accent
    case "completed":
    case "merged":
      return "#4f7942"; // success
    case "failed":
      return "#a02e2e"; // danger
    default:
      return "#6b6960"; // ink-muted
  }
}

type GraphViewProps = {
  graph: GraphSnapshot;
  selectedNodeId: string;
  onSelectNode: (nodeId: string) => void;
};

const nodeTypes = {
  worktree: WorktreeNode,
};

const edgeTypes = {
  animated: AnimatedEdge,
};

const NODE_WIDTH = 300;
const NODE_HEIGHT = 200;

function layoutWithDagre(graph: GraphSnapshot) {
  const g = new dagre.graphlib.Graph();
  g.setGraph({
    rankdir: "TB",
    nodesep: 56,
    ranksep: 110,
    marginx: 80,
    marginy: 80,
  });
  g.setDefaultEdgeLabel(() => ({}));

  for (const node of graph.nodes) {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }
  for (const edge of graph.edges) {
    g.setEdge(edge.source, edge.target);
  }

  dagre.layout(g);

  const positions = new Map<string, { x: number; y: number }>();
  for (const node of graph.nodes) {
    const layout = g.node(node.id);
    if (layout) {
      positions.set(node.id, {
        x: layout.x - NODE_WIDTH / 2,
        y: layout.y - NODE_HEIGHT / 2,
      });
    }
  }
  return positions;
}

export function GraphView({ graph, selectedNodeId, onSelectNode }: GraphViewProps) {
  const positions = useMemo(() => layoutWithDagre(graph), [graph]);

  const nodes = useMemo<WorktreeFlowNode[]>(
    () =>
      graph.nodes.map((node) => ({
        id: node.id,
        type: "worktree",
        position: positions.get(node.id) ?? { x: 180, y: 120 },
        data: node,
        selected: node.id === selectedNodeId,
        zIndex: node.id === selectedNodeId ? 20 : 1,
      })),
    [graph.nodes, positions, selectedNodeId],
  );

  const edges = useMemo<Edge[]>(() => {
    const nodeById = new Map(graph.nodes.map((node) => [node.id, node]));

    return graph.edges.map((edge) => {
      const targetNode = nodeById.get(edge.target);
      const isActive =
        targetNode?.status === "running" || targetNode?.status === "queued";
      const stroke = isActive
        ? "var(--color-accent)"
        : "var(--color-line-strong)";

      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        animated: isActive,
        type: isActive ? "animated" : "smoothstep",
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: stroke,
          width: 16,
          height: 16,
        },
        style: {
          stroke,
          strokeWidth: isActive ? 1.75 : 1,
        },
      };
    });
  }, [graph.edges, graph.nodes]);

  return (
    <ReactFlowProvider>
      <div className="blueprint-bg relative h-screen w-full overflow-hidden">
        <ReactFlow
          className="agent-graph-flow"
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          fitViewOptions={{ padding: 0.25, duration: 500 }}
          minZoom={0.4}
          maxZoom={1.4}
          onNodeClick={(_, node) => onSelectNode(node.id)}
          proOptions={{ hideAttribution: true }}
        >
          <Controls showInteractive={false} />
          {graph.nodes.length >= 4 ? (
            <MiniMap
              pannable
              zoomable
              ariaLabel="Graph minimap"
              maskColor="rgba(245, 241, 232, 0.7)"
              nodeColor={(n: RfNode) => statusColor((n.data as GraphNode).status)}
              nodeStrokeColor="rgba(26,26,29,0.22)"
              nodeStrokeWidth={2}
              nodeBorderRadius={3}
              style={{
                background: "var(--color-surface)",
                border: "1px solid var(--color-line)",
                borderRadius: 8,
                boxShadow: "0 1px 0 rgba(26,26,29,0.05), 0 12px 32px rgba(26,26,29,0.08)",
              }}
            />
          ) : null}
        </ReactFlow>
      </div>
    </ReactFlowProvider>
  );
}
