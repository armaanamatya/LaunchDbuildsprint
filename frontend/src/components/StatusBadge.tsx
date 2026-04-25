import type { NodeStatus } from "../types";

type BadgeStyle = { tone: string; dot: string; label: string; pulse?: boolean; glyph?: string };

const STATUS_STYLES: Record<NodeStatus, BadgeStyle> = {
  idle: { tone: "border-line text-ink-muted", dot: "bg-ink/25", label: "Idle" },
  queued: { tone: "border-line text-ink-muted", dot: "bg-ink/40", label: "Queued" },
  running: {
    tone: "border-[color:var(--color-accent)] bg-[color:var(--color-accent-soft)] text-[color:var(--color-accent)]",
    dot: "bg-[color:var(--color-accent)]",
    label: "Running",
    pulse: true,
  },
  completed: { tone: "border-line-strong text-ink", dot: "bg-ink", label: "Completed" },
  failed: {
    tone: "border-[color:var(--color-danger)]/30 text-[color:var(--color-danger)]",
    dot: "bg-[color:var(--color-danger)]",
    label: "Failed",
  },
  merged: { tone: "border-line-strong text-ink", dot: "bg-ink", label: "Merged", glyph: "✓" },
};

export function StatusBadge({ status }: { status: NodeStatus }) {
  const badge = STATUS_STYLES[status];
  return (
    <span className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-eyebrow ${badge.tone}`}>
      {badge.glyph
        ? <span className="text-[11px] leading-none">{badge.glyph}</span>
        : <span className={`h-1.5 w-1.5 rounded-full ${badge.dot} ${badge.pulse ? "accent-pulse" : ""}`} />}
      {badge.label}
    </span>
  );
}
