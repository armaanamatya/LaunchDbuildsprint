import {
  Controls,
  MarkerType,
  ReactFlow,
  ReactFlowProvider,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import dagre from "dagre";
import { useMemo } from "react";
import type { GraphSnapshot } from "../types";
import { WorktreeNode, type WorktreeFlowNode } from "./WorktreeNode";

type GraphViewProps = {
  graph: GraphSnapshot;
  selectedNodeId: string;
  onSelectNode: (nodeId: string) => void;
};

const nodeTypes = {
  worktree: WorktreeNode,
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
        type: "smoothstep",
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
          fitView
          fitViewOptions={{ padding: 0.25, duration: 500 }}
          minZoom={0.4}
          maxZoom={1.4}
          onNodeClick={(_, node) => onSelectNode(node.id)}
          proOptions={{ hideAttribution: true }}
        >
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </ReactFlowProvider>
  );
}
