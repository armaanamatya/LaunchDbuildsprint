import {
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  ReactFlow,
  ReactFlowProvider,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
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

const PRIMARY_CHILD_OFFSETS = [
  { x: 0, y: 360 },
  { x: 560, y: 210 },
  { x: 560, y: 510 },
  { x: 1040, y: 360 },
];

function buildNodePositions(graph: GraphSnapshot) {
  const childrenByParent = new Map<string | null, typeof graph.nodes>();

  for (const node of graph.nodes) {
    const siblings = childrenByParent.get(node.parent_id) ?? [];
    siblings.push(node);
    childrenByParent.set(node.parent_id, siblings);
  }

  const positions = new Map<string, { x: number; y: number }>();

  const placeChildren = (parentId: string, depth: number) => {
    const parentPosition = positions.get(parentId);
    const children = childrenByParent.get(parentId) ?? [];

    if (!parentPosition) {
      return;
    }

    children.forEach((child, index) => {
      let position = {
        x: parentPosition.x + 460,
        y: parentPosition.y + index * 280,
      };

      if (depth === 0) {
        const offset = PRIMARY_CHILD_OFFSETS[index] ?? {
          x: 1040 + index * 280,
          y: 280 + index * 180,
        };
        position = {
          x: parentPosition.x + offset.x,
          y: parentPosition.y + offset.y,
        };
      } else {
        const spread = (index - (children.length - 1) / 2) * 260;
        position = {
          x: parentPosition.x + 440,
          y: parentPosition.y + 220 + spread,
        };
      }

      positions.set(child.id, position);
      placeChildren(child.id, depth + 1);
    });
  };

  const roots = childrenByParent.get(null) ?? graph.nodes.filter((node) => node.parent_id === null);

  roots.forEach((root, index) => {
    positions.set(root.id, {
      x: 180 + index * 520,
      y: 110,
    });
    placeChildren(root.id, 0);
  });

  return positions;
}

export function GraphView({ graph, selectedNodeId, onSelectNode }: GraphViewProps) {
  const positions = useMemo(() => buildNodePositions(graph), [graph]);

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

  const edges = useMemo<Edge[]>(
    () => {
      const nodeById = new Map(graph.nodes.map((node) => [node.id, node]));

      return graph.edges.map((edge) => {
        const targetNode = nodeById.get(edge.target);
        const isActive =
          targetNode?.status === "running" || targetNode?.status === "queued";
        const stroke = isActive ? "rgba(248, 208, 138, 0.86)" : "rgba(255, 255, 255, 0.32)";

        return {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          animated: isActive,
          type: "smoothstep",
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: stroke,
            width: 18,
            height: 18,
          },
          style: {
            stroke,
            strokeWidth: isActive ? 2 : 1.5,
          },
        };
      });
    },
    [graph.edges, graph.nodes],
  );

  return (
    <ReactFlowProvider>
      <div className="relative h-screen w-full overflow-hidden bg-[#050607]">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(255,186,92,0.08),_transparent_18%),radial-gradient(circle_at_78%_24%,_rgba(255,255,255,0.03),_transparent_22%),linear-gradient(180deg,_rgba(3,4,5,0.72),_rgba(3,4,5,0.96))]" />
        <ReactFlow
          className="agent-graph-flow"
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2, duration: 500 }}
          minZoom={0.45}
          maxZoom={1.35}
          onNodeClick={(_, node) => onSelectNode(node.id)}
          proOptions={{ hideAttribution: true }}
        >
          <Background
            id="minor-grid"
            color="rgba(255,255,255,0.035)"
            gap={24}
            size={1}
            variant={BackgroundVariant.Lines}
          />
          <Background
            id="major-grid"
            color="rgba(255,255,255,0.045)"
            gap={120}
            size={1}
            variant={BackgroundVariant.Lines}
          />
          <Controls />
        </ReactFlow>
      </div>
    </ReactFlowProvider>
  );
}
