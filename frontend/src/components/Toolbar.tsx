type ToolbarProps = {
  baseBranch: string;
  onOpenCreate: () => void;
  onOpenCompare: () => void;
  onReset: () => void;
  canCompare: boolean;
  completedCount: number;
  showAdvancedActions: boolean;
};

export function Toolbar({
  baseBranch,
  onOpenCreate,
  onOpenCompare,
  onReset,
  canCompare,
  completedCount,
  showAdvancedActions,
}: ToolbarProps) {
  const compareLabel = canCompare ? `Compare ${completedCount} →` : "Compare";
  const branchIsLong = baseBranch.length > 18;

  return (
    <div className="inline-flex max-w-full flex-wrap items-center gap-2 rounded-full border border-line bg-surface px-3 py-2 shadow-panel">
      {/* Identity */}
      <div className="flex items-center gap-2 pl-1 pr-2">
        <span className="h-1.5 w-1.5 rounded-full bg-ink" />
        <p className="font-display text-[15px] font-semibold tracking-[-0.02em] text-ink">
          Agent Graph
        </p>
        <span
          className={`rounded-full border border-line bg-paper px-2 py-0.5 text-[10px] font-semibold text-ink-muted ${
            branchIsLong
              ? "max-w-[14ch] truncate normal-case tracking-[0.04em]"
              : "uppercase tracking-[0.16em]"
          }`}
          title={baseBranch}
        >
          {branchIsLong ? baseBranch : baseBranch.toUpperCase()}
        </span>
      </div>

      <div className="hidden h-5 w-px bg-line sm:block" />

      {/* Primary entry-point — secondary tier (the empty-state hero owns the dominant CTA) */}
      <button
        type="button"
        onClick={onOpenCreate}
        className="rounded-full border border-line bg-paper px-3 py-1.5 text-sm font-semibold text-ink hover:border-line-strong"
      >
        + New branch
      </button>

      {showAdvancedActions && (
        <>
          <div className="hidden h-5 w-px bg-line sm:block" />
          <button
            type="button"
            onClick={onOpenCompare}
            disabled={!canCompare}
            className={
              canCompare
                ? "rounded-full bg-ink px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-paper hover:bg-ink/90"
                : "rounded-full border border-line/50 bg-paper px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-ink-soft cursor-not-allowed"
            }
          >
            {compareLabel}
          </button>
          <button
            type="button"
            onClick={onReset}
            className="rounded-full px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-ink-muted hover:text-[color:var(--color-danger)]"
          >
            Reset
          </button>
        </>
      )}
    </div>
  );
}
