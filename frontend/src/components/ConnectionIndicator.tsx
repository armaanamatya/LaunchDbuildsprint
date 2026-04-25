import { useGraphStore } from "../store/graphStore";

type ResolvedStyle = { dot: string; label: string };

function resolve(
  status: "connecting" | "open" | "reconnecting" | "closed",
  hasEverConnected: boolean,
): ResolvedStyle {
  if (status === "open") return { dot: "bg-ink", label: "Live" };
  if (status === "closed") return { dot: "bg-[color:var(--color-danger)]", label: "Offline" };
  // connecting / reconnecting
  const label = hasEverConnected ? "Reconnecting" : "Connecting";
  return { dot: "bg-[color:var(--color-accent)] accent-pulse", label };
}

export function ConnectionIndicator() {
  const status = useGraphStore((s) => s.connection);
  const hasEverConnected = useGraphStore((s) => s.hasEverConnected);
  const s = resolve(status, hasEverConnected);
  return (
    <div className="pointer-events-auto flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1.5 text-[11px] font-medium text-ink-muted shadow-panel">
      <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
      {s.label}
    </div>
  );
}
