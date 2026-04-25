import type { NodeStatus } from "../types";

const STATUS_STYLES: Record<
  NodeStatus,
  { tone: string; dot: string; label: string }
> = {
  idle: {
    tone: "border-white/10 bg-white/[0.04] text-white/55",
    dot: "bg-white/35",
    label: "Idle",
  },
  queued: {
    tone: "border-amber-400/15 bg-amber-400/10 text-amber-100",
    dot: "bg-amber-300",
    label: "Queued",
  },
  running: {
    tone: "border-sky-400/15 bg-sky-400/10 text-sky-100",
    dot: "bg-sky-300",
    label: "Running",
  },
  completed: {
    tone: "border-emerald-400/15 bg-emerald-400/10 text-emerald-100",
    dot: "bg-emerald-300",
    label: "Completed",
  },
  failed: {
    tone: "border-rose-400/15 bg-rose-400/10 text-rose-100",
    dot: "bg-rose-300",
    label: "Failed",
  },
  merged: {
    tone: "border-lime-400/15 bg-lime-400/10 text-lime-100",
    dot: "bg-lime-300",
    label: "Merged",
  },
};

type StatusBadgeProps = {
  status: NodeStatus;
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const badge = STATUS_STYLES[status];

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] ${badge.tone}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${badge.dot}`} />
      {badge.label}
    </span>
  );
}
