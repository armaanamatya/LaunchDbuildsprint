type StatusStripProps = {
  branchCount: number;
};

export function StatusStrip({ branchCount }: StatusStripProps) {
  const branchesLabel = `${branchCount} ${branchCount === 1 ? "branch" : "branches"}`;
  return (
    <div className="inline-flex items-center gap-3 rounded-full border border-line bg-surface px-4 py-2 text-[11px] font-medium text-ink-muted shadow-panel">
      <span className="font-semibold text-ink">{branchesLabel}</span>
      <span className="h-3 w-px bg-line" aria-hidden />
      <span className="font-mono text-[10.5px] text-ink-soft">on canvas</span>
    </div>
  );
}
