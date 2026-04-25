type ToolbarProps = {
  baseBranch: string;
  onCreateBranch: () => void;
};

export function Toolbar({ baseBranch, onCreateBranch }: ToolbarProps) {
  return (
    <div className="flex flex-wrap items-center gap-4 rounded-[1.75rem] border border-white/10 bg-[#0d0f11]/82 px-4 py-3 shadow-[0_18px_60px_rgba(0,0,0,0.42)] backdrop-blur-2xl">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_18px_rgba(74,222,128,0.65)]" />
          <p className="font-display text-lg font-semibold tracking-[-0.03em] text-white">
            Agent Graph
          </p>
          <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/60">
            {baseBranch}
          </span>
        </div>
        <p className="mt-1 text-sm text-white/45">
          Branch, compare, choose, and merge without losing the graph.
        </p>
      </div>
      <button
        type="button"
        onClick={onCreateBranch}
        className="rounded-full border border-amber-400/30 bg-[linear-gradient(180deg,rgba(251,191,36,0.18),rgba(251,191,36,0.08))] px-4 py-2.5 text-sm font-semibold text-amber-50 transition duration-200 hover:border-amber-300/50 hover:bg-[linear-gradient(180deg,rgba(251,191,36,0.24),rgba(251,191,36,0.12))]"
      >
        + New branch
      </button>
    </div>
  );
}
