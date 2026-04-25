import type { NodeStatus } from "../types";

type BadgeStyle = { tone: string; dot: string; label: string; pulse?: boolean; glyph?: string };

const STATUS_STYLES: Record<NodeStatus, BadgeStyle> = {
  idle: { tone: "border-line text-ink-soft", dot: "bg-ink/25", label: "Idle" },
  queued: { tone: "border-line text-ink-muted", dot: "bg-ink-muted", label: "Queued", pulse: true },
  running: {
    tone: "border-[color:var(--color-accent)]/30 bg-[color:var(--color-accent-soft)] text-[color:var(--color-accent-strong)]",
    dot: "bg-[color:var(--color-accent)]",
    label: "Running",
    pulse: true,
  },
  completed: {
    tone: "border-[color:var(--color-success)]/30 bg-success-soft text-[color:var(--color-success)]",
    dot: "bg-[color:var(--color-success)]",
    label: "Completed",
  },
  failed: {
    tone: "border-[color:var(--color-danger)]/30 bg-danger-soft text-[color:var(--color-danger)]",
    dot: "bg-[color:var(--color-danger)]",
    label: "Failed",
  },
  merged: {
    tone: "border-[color:var(--color-success)] bg-[color:var(--color-success)] text-paper",
    dot: "bg-paper",
    label: "Merged",
    glyph: "✓",
  },
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
