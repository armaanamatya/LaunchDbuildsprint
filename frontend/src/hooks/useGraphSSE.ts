import { useEffect } from "react";
import { openSSE } from "../api/sse";
import { useGraphStore } from "../store/graphStore";

export function useGraphSSE() {
  const ingest = useGraphStore((s) => s.ingest);
  const setConnection = useGraphStore((s) => s.setConnection);

  useEffect(() => {
    const dispose = openSSE("/api/v1/graph/sse", {
      onEvent: (event) => ingest(event),
      onStatus: (status) => setConnection(status),
    });
    return dispose;
  }, [ingest, setConnection]);
}
