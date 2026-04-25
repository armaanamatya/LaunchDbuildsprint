import { BaseEdge, getSmoothStepPath, type EdgeProps } from "@xyflow/react";

/**
 * Smoothstep edge that emits a small accent-coloured particle riding the path
 * from source to target. Used while a downstream node is running/queued —
 * gives a literal sense of work flowing along the wire.
 */
export function AnimatedEdge(props: EdgeProps) {
  const [path] = getSmoothStepPath({
    sourceX: props.sourceX,
    sourceY: props.sourceY,
    targetX: props.targetX,
    targetY: props.targetY,
    sourcePosition: props.sourcePosition,
    targetPosition: props.targetPosition,
  });

  return (
    <>
      <BaseEdge
        id={props.id}
        path={path}
        markerEnd={props.markerEnd}
        style={props.style}
      />
      <circle
        r={3}
        className="edge-particle"
        style={{ offsetPath: `path('${path}')` }}
      />
    </>
  );
}
