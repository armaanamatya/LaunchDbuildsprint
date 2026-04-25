type ToolbarProps = {
  baseBranch: string;
  onOpenCreate: () => void;
  onQuickStart: () => void;
  onOpenCompare: () => void;
  onReset: () => void;
  canCompare: boolean;
  showAdvancedActions: boolean;
};

export function Toolbar({
  baseBranch,
  onOpenCreate,
  onQuickStart,
  onOpenCompare,
  onReset,
  canCompare,
  showAdvancedActions,
}: ToolbarProps) {
  return (
    <div className="inline-flex max-w-full flex-wrap items-center gap-2 rounded-full border border-white/10 bg-[#0d0f11]/82 px-3 py-2 shadow-[0_18px_60px_rgba(0,0,0,0.42)] backdrop-blur-2xl">
      <div className="flex items-center gap-2 pl-1 pr-2">
        <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_18px_rgba(74,222,128,0.65)]" />
        <p className="font-display text-base font-semibold tracking-[-0.02em] text-white">
          Agent Graph
        </p>
        <span className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/60">
          {baseBranch}
        </span>
      </div>

      {showAdvancedActions && (
        <>
          <div className="hidden h-5 w-px bg-white/10 sm:block" />
          <button
            type="button"
            onClick={onQuickStart}
            className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-white/75 hover:bg-white/[0.08]"
            title="Spawn 3 branches with the locked hero prompt"
          >
            Quick start ×3
          </button>
          <button
            type="button"
            onClick={onOpenCompare}
            disabled={!canCompare}
            className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-white/75 hover:bg-white/[0.08] disabled:opacity-40"
          >
            Compare
          </button>
          <button
            type="button"
            onClick={onReset}
            className="rounded-full border border-rose-400/25 bg-rose-400/10 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-rose-100 hover:bg-rose-400/15"
          >
            Reset
          </button>
        </>
      )}

      <button
        type="button"
        onClick={onOpenCreate}
        className="rounded-full border border-amber-400/30 bg-[linear-gradient(180deg,rgba(251,191,36,0.18),rgba(251,191,36,0.08))] px-4 py-1.5 text-sm font-semibold text-amber-50 transition duration-150 hover:border-amber-300/50 hover:bg-[linear-gradient(180deg,rgba(251,191,36,0.24),rgba(251,191,36,0.12))]"
      >
        + New branch
      </button>
    </div>
  );
}
