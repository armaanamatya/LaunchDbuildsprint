import type { NodeStrategy } from "../types";

const STRATEGY_META: Record<
  NodeStrategy,
  { initial: string; label: string; tint: string; dot: string }
> = {
  route_local: {
    initial: "L",
    label: "Route-local",
    tint: "text-[color:var(--strategy-route-local)]",
    dot: "bg-[color:var(--strategy-route-local)]",
  },
  dependency: {
    initial: "D",
    label: "Dependency",
    tint: "text-[color:var(--strategy-dependency)]",
    dot: "bg-[color:var(--strategy-dependency)]",
  },
  middleware: {
    initial: "M",
    label: "Middleware",
    tint: "text-[color:var(--strategy-middleware)]",
    dot: "bg-[color:var(--strategy-middleware)]",
  },
};

/**
 * Persona-style avatar showing which architectural strategy the agent took.
 * The avatar lives on the WorktreeNode; the full label appears in DetailPanel.
 */
export function StrategyAvatar({ strategy }: { strategy: NodeStrategy }) {
  const meta = STRATEGY_META[strategy];
  return (
    <span
      className={`inline-flex h-6 w-6 items-center justify-center rounded-full border border-line font-mono text-[11px] font-medium ${meta.tint}`}
      title={meta.label}
      aria-label={`Strategy: ${meta.label}`}
    >
      {meta.initial}
    </span>
  );
}

export function StrategyChip({ strategy }: { strategy: NodeStrategy }) {
  const meta = STRATEGY_META[strategy];
  return (
    <span className="inline-flex items-center gap-1.5 rounded-sm border border-line bg-paper-deep px-2 py-0.5 font-mono text-[10px] uppercase tracking-eyebrow text-ink-muted">
      <span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />
      {meta.label}
    </span>
  );
}
