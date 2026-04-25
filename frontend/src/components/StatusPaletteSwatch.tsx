const STATUSES = [
  { key: "idle",      label: "IDLE",      fg: "var(--status-idle-fg)",      bg: "var(--status-idle-bg)",      border: "var(--status-idle-border)" },
  { key: "creating",  label: "CREATING",  fg: "var(--status-creating-fg)",  bg: "var(--status-creating-bg)",  border: "var(--status-creating-border)" },
  { key: "running",   label: "RUNNING",   fg: "var(--status-running-fg)",   bg: "var(--status-running-bg)",   border: "var(--status-running-border)" },
  { key: "completed", label: "COMPLETED", fg: "var(--status-completed-fg)", bg: "var(--status-completed-bg)", border: "var(--status-completed-border)" },
  { key: "failed",    label: "FAILED",    fg: "var(--status-failed-fg)",    bg: "var(--status-failed-bg)",    border: "var(--status-failed-border)" },
  { key: "merged",    label: "MERGED",    fg: "var(--status-merged-fg)",    bg: "var(--status-merged-bg)",    border: "var(--status-merged-border)" },
];

export function StatusPaletteSwatch() {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "var(--color-bg-canvas)" }}
    >
      <div className="flex flex-col gap-3 p-6">
        <h1 className="font-mono text-md text-text-primary">Status palette</h1>
        <div className="flex gap-3">
          {STATUSES.map((s) => (
            <div
              key={s.key}
              className="flex flex-col items-center gap-1 rounded-md border p-3"
              style={{
                background: s.bg,
                borderColor: s.border,
                color: s.fg,
                minWidth: 120,
              }}
            >
              <span className="h-2 w-2 rounded-full" style={{ background: s.fg }} />
              <span className="font-mono text-xs tracking-eyebrow">{s.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
