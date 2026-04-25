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
  const dialogRef = useRef<HTMLDivElement>(null);
  const labelRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    setLabel("Approach");
    setPrompt(defaultPrompt);
    requestAnimationFrame(() => labelRef.current?.focus());
  }, [open, defaultPrompt]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        return;
      }
      if (e.key === "Tab" && dialogRef.current) {
        const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        void submit();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

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
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="cbm-title"
        className="w-full max-w-lg rounded-lg border border-line bg-surface p-6 shadow-panel-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <p className="font-mono text-[10px] font-medium uppercase tracking-eyebrow text-accent">
          New branch
        </p>
        <h2 id="cbm-title" className="mt-1 font-display text-2xl font-medium leading-tight tracking-[-0.025em] text-ink">
          Spawn an implementation path
        </h2>

        <label
          htmlFor="cbm-label"
          className="mt-6 block font-mono text-[10px] font-medium uppercase tracking-eyebrow text-ink-soft"
        >
          Label
        </label>
        <input
          id="cbm-label"
          ref={labelRef}
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          className="mt-1.5 w-full rounded-sm border border-line bg-paper-deep px-3 py-2 text-[13px] text-ink outline-none transition focus:border-accent focus:bg-surface"
        />

        <label
          htmlFor="cbm-prompt"
          className="mt-4 block font-mono text-[10px] font-medium uppercase tracking-eyebrow text-ink-soft"
        >
          Prompt
        </label>
        <textarea
          id="cbm-prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={6}
          className="mt-1.5 w-full resize-none rounded-sm border border-line bg-paper-deep px-3 py-2 text-[13px] leading-6 text-ink outline-none transition focus:border-accent focus:bg-surface"
        />

        <div className="mt-6 flex items-center justify-between">
          <p className="font-mono text-[10px] uppercase tracking-eyebrow text-ink-soft">
            <kbd className="rounded-sm border border-line bg-paper-deep px-1.5 py-0.5 text-ink-muted">⌘ ↵</kbd> to create · <kbd className="rounded-sm border border-line bg-paper-deep px-1.5 py-0.5 text-ink-muted">Esc</kbd> to cancel
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="rounded-sm border border-line bg-surface px-3 py-1.5 font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-muted hover:bg-paper-deep hover:text-ink"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={submit}
              disabled={submitting || !label.trim() || !prompt.trim()}
              className="rounded-sm border border-[color:var(--color-accent)] bg-accent px-3 py-1.5 font-mono text-[11px] font-medium uppercase tracking-eyebrow text-white transition hover:bg-accent-strong disabled:opacity-50"
            >
              {submitting ? "Creating…" : "Create"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
