import { useEffect } from "react";
import { openSSE } from "../api/sse";
import { useGraphStore } from "../store/graphStore";

/**
 * Subscribe to per-node events for a specific node id. Returns a cleanup fn.
 * Use only when the global /graph/sse stream is insufficient (e.g. high-frequency
 * agent.text events on the focused node). Backend filters by node_id.
 */
export function useNodeSSE(nodeId: string | null) {
  const ingest = useGraphStore((s) => s.ingest);
  useEffect(() => {
    if (!nodeId || nodeId === "root") return;
    const dispose = openSSE(`/api/v1/nodes/${nodeId}/sse`, {
      onEvent: (event) => ingest(event),
      onStatus: () => {},
    });
    return dispose;
  }, [nodeId, ingest]);
}
