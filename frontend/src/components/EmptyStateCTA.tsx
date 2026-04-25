type Props = { onQuickStart: () => void; onCreate: () => void };

export function EmptyStateCTA({ onQuickStart, onCreate }: Props) {
  return (
    <div className="pointer-events-auto absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2 rounded-3xl border border-white/10 bg-[#0d0f11]/85 p-6 text-center shadow-[0_30px_80px_rgba(0,0,0,0.55)] backdrop-blur-2xl">
      <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-white/40">
        Start the demo
      </p>
      <h2 className="mt-2 font-display text-2xl font-semibold tracking-[-0.03em] text-white">
        Spawn three implementation paths
      </h2>
      <p className="mt-2 max-w-sm text-sm text-white/60">
        Each branch runs an isolated agent in its own git worktree. Compare the
        diffs side by side, pick the winner, merge.
      </p>
      <div className="mt-5 flex justify-center gap-2">
        <button
          type="button"
          onClick={onQuickStart}
          className="rounded-full border border-amber-400/30 bg-[linear-gradient(180deg,rgba(251,191,36,0.18),rgba(251,191,36,0.08))] px-4 py-2 text-sm font-semibold text-amber-50 hover:border-amber-300/50"
        >
          Quick start ×3
        </button>
        <button
          type="button"
          onClick={onCreate}
          className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-white/80 hover:bg-white/[0.08]"
        >
          New branch
        </button>
      </div>
    </div>
  );
}
