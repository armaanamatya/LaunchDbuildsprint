import { useGraphStore } from "../store/graphStore";

const STYLES = {
  connecting:   { dot: "bg-[color:var(--color-accent)] animate-pulse", label: "Connecting" },
  open:         { dot: "bg-success",                                    label: "Live" },
  reconnecting: { dot: "bg-[color:var(--color-accent)] animate-pulse", label: "Reconnecting" },
  closed:       { dot: "bg-danger",                                     label: "Offline" },
} as const;

export function ConnectionIndicator() {
  const status = useGraphStore((s) => s.connection);
  const s = STYLES[status];
  return (
    <div className="pointer-events-auto flex items-center gap-2 rounded-sm border border-line bg-surface px-3 py-1.5 font-mono text-[10.5px] font-medium uppercase tracking-eyebrow text-ink-muted shadow-panel">
      <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
      {s.label}
    </div>
  );
}
