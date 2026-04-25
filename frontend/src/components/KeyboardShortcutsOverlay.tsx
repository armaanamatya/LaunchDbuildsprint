import { useEffect } from "react";

type Props = { open: boolean; onClose: () => void };

const SHORTCUTS: { keys: string; label: string }[] = [
  { keys: "N", label: "New branch" },
  { keys: "R", label: "Run selected branch" },
  { keys: "C", label: "Open compare" },
  { keys: "M", label: "Merge selected branch" },
  { keys: "?", label: "Show this overlay" },
  { keys: "Esc", label: "Close any overlay" },
];

export function KeyboardShortcutsOverlay({ open, onClose }: Props) {
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/30 px-4"
      role="dialog"
      aria-modal="true"
      aria-label="Keyboard shortcuts"
      onClick={onClose}
    >
      <div
        className="w-full max-w-sm rounded-lg border border-line bg-surface p-5 shadow-panel-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <p className="font-mono text-[10px] font-medium uppercase tracking-eyebrow text-accent">
          Shortcuts
        </p>
        <h2 className="mt-1 font-display text-xl font-medium tracking-[-0.025em] text-ink">
          Keyboard
        </h2>
        <ul className="mt-4 divide-y divide-line">
          {SHORTCUTS.map((s) => (
            <li key={s.keys} className="flex items-center justify-between py-2 font-mono text-[12px]">
              <span className="text-ink">{s.label}</span>
              <kbd className="rounded-sm border border-line bg-paper-deep px-2 py-0.5 text-ink-muted">
                {s.keys}
              </kbd>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
