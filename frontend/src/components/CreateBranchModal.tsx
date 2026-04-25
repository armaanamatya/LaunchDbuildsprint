import { useEffect, useRef, useState } from "react";

type Props = {
  open: boolean;
  defaultPrompt: string;
  onSubmit: (label: string, prompt: string) => Promise<void> | void;
  onClose: () => void;
};

export function CreateBranchModal({ open, defaultPrompt, onSubmit, onClose }: Props) {
  const [label, setLabel] = useState("Approach");
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [submitting, setSubmitting] = useState(false);
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (open) {
      setLabel("Approach");
      setPrompt(defaultPrompt);
      requestAnimationFrame(() => ref.current?.focus());
    }
  }, [open, defaultPrompt]);

  if (!open) return null;

  const submit = async () => {
    if (!label.trim() || !prompt.trim()) return;
    setSubmitting(true);
    try {
      await onSubmit(label.trim(), prompt.trim());
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-3xl border border-white/10 bg-[#0d0f11] p-6 shadow-[0_30px_120px_rgba(0,0,0,0.7)]"
        onClick={(e) => e.stopPropagation()}
      >
        <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-white/40">
          New branch
        </p>
        <h2 className="mt-2 font-display text-2xl font-semibold tracking-[-0.03em] text-white">
          Spawn an implementation path
        </h2>

        <label className="mt-6 block text-[11px] font-semibold uppercase tracking-[0.22em] text-white/50">
          Label
        </label>
        <input
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          className="mt-2 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-sm text-white outline-none focus:border-amber-300/40"
        />

        <label className="mt-4 block text-[11px] font-semibold uppercase tracking-[0.22em] text-white/50">
          Prompt
        </label>
        <textarea
          ref={ref}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={6}
          className="mt-2 w-full resize-none rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-sm leading-6 text-white outline-none focus:border-amber-300/40"
        />

        <div className="mt-6 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-white/10 px-4 py-2 text-sm text-white/70 hover:bg-white/5"
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={submitting || !label.trim() || !prompt.trim()}
            className="rounded-full border border-amber-400/30 bg-[linear-gradient(180deg,rgba(251,191,36,0.18),rgba(251,191,36,0.08))] px-4 py-2 text-sm font-semibold text-amber-50 hover:border-amber-300/50 disabled:opacity-50"
          >
            {submitting ? "Creating…" : "Create branch"}
          </button>
        </div>
      </div>
    </div>
  );
}
