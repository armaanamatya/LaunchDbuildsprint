import type { GraphEvent, GraphEventType } from "../types";

type Handlers = {
  onEvent: (e: GraphEvent) => void;
  onStatus: (s: "connecting" | "open" | "reconnecting" | "closed") => void;
};

const EVENT_TYPES: GraphEventType[] = [
  "graph.connected",
  "node.created",
  "node.updated",
  "node.deleted",
  "node.run_queued",
  "node.merged",
  "node.diff_ready",
  "agent.started",
  "agent.text",
  "agent.tool_use",
  "agent.tool_result",
  "agent.completed",
  "agent.failed",
  "heartbeat",
];

export function openSSE(url: string, handlers: Handlers): () => void {
  let closed = false;
  let attempt = 0;
  let source: EventSource | null = null;
  let retryTimer: ReturnType<typeof setTimeout> | null = null;

  const dispatch = (msg: MessageEvent) => {
    try {
      const parsed = JSON.parse(msg.data) as GraphEvent;
      handlers.onEvent(parsed);
    } catch {
      // Ignore malformed events.
    }
  };

  const connect = () => {
    handlers.onStatus(attempt === 0 ? "connecting" : "reconnecting");
    source = new EventSource(url);

    source.onopen = () => {
      attempt = 0;
      handlers.onStatus("open");
    };

    // Register a listener per named event type — the backend uses `event:` lines
    // so onmessage will not fire for any of these.
    for (const type of EVENT_TYPES) {
      source.addEventListener(type, dispatch as EventListener);
    }
    // Fallback for any unnamed events (defensive).
    source.onmessage = dispatch;

    source.onerror = () => {
      source?.close();
      if (closed) return;
      attempt += 1;
      const delay = Math.min(1000 * 2 ** Math.min(attempt - 1, 5), 15000);
      handlers.onStatus("reconnecting");
      retryTimer = setTimeout(connect, delay);
    };
  };

  connect();

  return () => {
    closed = true;
    if (retryTimer) clearTimeout(retryTimer);
    source?.close();
    handlers.onStatus("closed");
  };
}
