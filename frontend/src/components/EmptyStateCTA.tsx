type Props = { onQuickStart: () => void; onCreate: () => void };

export function EmptyStateCTA({ onQuickStart, onCreate }: Props) {
  return (
    <div className="pointer-events-auto absolute left-1/2 top-1/2 z-10 w-[min(540px,92vw)] -translate-x-1/2 -translate-y-1/2 rounded-xl border border-line bg-surface-raised p-7 text-center shadow-panel-lg">
      <p className="font-mono text-[10px] font-semibold uppercase tracking-eyebrow text-ink-muted">
        Start the demo
      </p>
      <h2 className="mt-3 font-display text-[2rem] font-semibold leading-tight tracking-[-0.025em] text-ink">
        Spawn three implementation paths
      </h2>
      <p className="mx-auto mt-3 max-w-md text-[14px] leading-6 text-ink-muted">
        Each branch runs an isolated agent in its own git worktree. Compare the
        diffs side by side, pick the winner, merge.
      </p>
      <div className="mt-6 flex justify-center gap-2">
        <button
          type="button"
          onClick={onQuickStart}
          className="rounded-sm border border-[color:var(--color-accent)] bg-accent px-4 py-2 font-mono text-[11px] font-semibold uppercase tracking-eyebrow text-white transition hover:bg-accent-strong"
        >
          Quick start ×3
        </button>
        <button
          type="button"
          onClick={onCreate}
          className="rounded-sm border border-line bg-surface px-4 py-2 font-mono text-[11px] font-semibold uppercase tracking-eyebrow text-ink-muted transition hover:bg-paper-deep hover:text-ink"
        >
          New branch
        </button>
      </div>
    </div>
  );
}
