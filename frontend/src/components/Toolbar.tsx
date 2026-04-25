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
    <div className="inline-flex max-w-full flex-wrap items-center gap-2 rounded-lg border border-line bg-surface px-3 py-2 shadow-panel">
      <div className="flex items-center gap-2 pl-1 pr-1">
        <span className="font-display text-[1.4rem] leading-none text-accent" aria-hidden>
          ⌐
        </span>
        <p className="font-display text-[1.05rem] font-medium tracking-[-0.015em] text-ink">
          Agent Graph
        </p>
        <span className="ml-1 rounded-sm border border-line bg-paper-deep px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-eyebrow text-ink-muted">
          {baseBranch}
        </span>
      </div>

      {showAdvancedActions && (
        <>
          <div className="hidden h-5 w-px bg-line sm:block" />
          <ToolbarButton onClick={onQuickStart} title="Spawn 3 branches with the locked hero prompt">
            Quick start ×3
          </ToolbarButton>
          <ToolbarButton onClick={onOpenCompare} disabled={!canCompare}>
            Compare
          </ToolbarButton>
          <ToolbarButton onClick={onReset} variant="danger">
            Reset
          </ToolbarButton>
        </>
      )}

      <button
        type="button"
        onClick={onOpenCreate}
        className="rounded-sm border border-[color:var(--color-accent)] bg-accent px-3 py-1 font-mono text-[11px] font-medium uppercase tracking-eyebrow text-white transition hover:bg-accent-strong"
      >
        + New branch
      </button>
    </div>
  );
}

function ToolbarButton({
  onClick,
  disabled,
  title,
  variant = "default",
  children,
}: {
  onClick: () => void;
  disabled?: boolean;
  title?: string;
  variant?: "default" | "danger";
  children: React.ReactNode;
}) {
  const tone =
    variant === "danger"
      ? "border-[color:var(--color-danger)]/30 bg-danger-soft text-danger hover:bg-[color:var(--color-danger)] hover:text-white"
      : "border-line bg-surface text-ink-muted hover:bg-paper-deep hover:text-ink";
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`rounded-sm border px-2.5 py-1 font-mono text-[10.5px] font-medium uppercase tracking-eyebrow transition disabled:opacity-40 ${tone}`}
    >
      {children}
    </button>
  );
}
