import { useState } from "react";

type Props = {
  defaultPrompt: string;
  onSubmit: (prompt: string) => Promise<void> | void;
  onCreate: () => void;
};

export function EmptyStateCTA({ defaultPrompt, onSubmit, onCreate }: Props) {
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    if (!prompt.trim() || submitting) return;
    setSubmitting(true);
    try {
      await onSubmit(prompt.trim());
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="pointer-events-auto absolute left-1/2 top-[44%] z-10 w-[min(620px,92vw)] -translate-x-1/2 -translate-y-1/2 text-center">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-ink-muted">
        Branching workspace for software decisions
      </p>
      <h2 className="mt-4 font-display text-[2.6rem] font-semibold leading-[1.05] tracking-[-0.035em] text-ink">
        What should we build
        <br />
        three ways?
      </h2>
      <p className="mx-auto mt-4 max-w-[520px] text-[14px] leading-6 text-ink-muted">
        Three agents will work on the same task in isolated git worktrees.
        Compare the diffs side by side, pick the winner, merge.
      </p>

      <div className="mt-7 rounded-2xl border border-line-strong bg-surface p-3 text-left shadow-panel">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={6}
          spellCheck={false}
          placeholder="Describe a small backend change…"
          className="block max-h-[280px] w-full resize-none overflow-y-auto rounded-xl bg-surface px-3 py-3 font-mono text-[12.5px] leading-6 text-ink outline-none placeholder:text-ink-muted/60"
          style={{
            maskImage:
              "linear-gradient(to bottom, transparent 0, #000 8px, #000 calc(100% - 8px), transparent 100%)",
            WebkitMaskImage:
              "linear-gradient(to bottom, transparent 0, #000 8px, #000 calc(100% - 8px), transparent 100%)",
          }}
        />
        <div className="flex items-center justify-between gap-3 px-2 pb-1 pt-2">
          <button
            type="button"
            onClick={onCreate}
            className="inline-flex items-center gap-1.5 rounded-full px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-muted hover:bg-paper-deep hover:text-ink"
          >
            <span aria-hidden>+</span> One branch at a time
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={submitting || !prompt.trim()}
            className="rounded-full bg-ink px-5 py-2.5 text-sm font-semibold text-paper hover:bg-ink/90 disabled:bg-ink/30"
          >
            {submitting ? "Spawning…" : "Spawn 3 branches →"}
          </button>
        </div>
      </div>
    </div>
  );
}
