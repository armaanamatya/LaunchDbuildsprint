import { useState } from "react";
import { AgentLogPanel } from "./AgentLogPanel";
import { DiffPanel } from "./DiffPanel";
import { StatusBadge } from "./StatusBadge";
import { StrategyChip } from "./StrategyBadge";
import { useGraphStore } from "../store/graphStore";
import type { AgentLogEntry, GraphNode } from "../types";

type Tab = "overview" | "logs" | "diff";

const EMPTY_LOGS: AgentLogEntry[] = [];

function compactPath(path: string) {
  const segments = path.split(/[/\\]+/).filter(Boolean);
  return segments.length <= 3 ? path : `…/${segments.slice(-3).join("/")}`;
}

function formatTimestamp(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Awaiting activity";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

export function DetailPanel({
  node,
  onClose,
}: {
  node: GraphNode;
  onClose?: () => void;
}) {
  const [tab, setTab] = useState<Tab>("overview");
  const logs = useGraphStore((s) => s.agentLogs[node.id] ?? EMPTY_LOGS);
  const runBranch = useGraphStore((s) => s.runBranch);
  const mergeBranch = useGraphStore((s) => s.mergeBranch);
  const deleteBranch = useGraphStore((s) => s.deleteBranch);
  const toggleCompareNode = useGraphStore((s) => s.toggleCompareNode);
  const compare = useGraphStore((s) => s.compare);

  const isRoot = node.parent_id === null;
  const canRun = !isRoot && (node.status === "idle" || node.status === "failed");
  const canMerge = node.status === "completed";
  const canDelete = !isRoot && node.status !== "running";
  const inCompare = compare.nodeIds.includes(node.id);
  const evalReady = node.eval_passed !== null && node.eval_passed !== undefined;

  return (
    <aside className="pointer-events-auto flex h-full w-full max-w-[26rem] flex-col overflow-y-auto rounded-2xl border border-line bg-surface-raised p-5 shadow-panel-lg">
      {/* Header eyebrow row */}
      <div className="flex items-center justify-between text-[10px] font-semibold uppercase tracking-[0.18em] text-ink-soft">
        <span>Selected branch</span>
        <div className="flex items-center gap-2">
          {node.strategy ? <StrategyChip strategy={node.strategy} /> : null}
          {onClose ? (
            <button
              type="button"
              onClick={onClose}
              aria-label="Close panel"
              className="rounded-full px-2 py-1 text-ink-muted hover:bg-paper-deep hover:text-ink"
            >
              ×
            </button>
          ) : null}
        </div>
      </div>

      {/* Title block */}
      <div className="mt-3 flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="font-display text-[1.5rem] font-semibold leading-tight tracking-[-0.025em] text-ink">
            {node.label}
          </h1>
          <p className="mt-0.5 truncate font-mono text-[12px] text-ink-soft">
            {node.branch_name}
          </p>
        </div>
        <StatusBadge status={node.status} />
      </div>

      {/* Action row — Merge primary, Run/Add-to-compare secondary, Delete quiet-destructive (right-aligned) */}
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => void mergeBranch(node.id)}
          disabled={!canMerge}
          className="rounded-full bg-ink px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-paper hover:bg-ink/90 disabled:bg-ink/30 disabled:cursor-not-allowed"
        >
          Merge
        </button>
        <button
          type="button"
          onClick={() => void runBranch(node.id)}
          disabled={!canRun}
          className="rounded-full border border-line bg-paper px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-ink hover:border-line-strong disabled:border-line/50 disabled:text-ink-soft disabled:cursor-not-allowed disabled:hover:border-line/50"
        >
          Run
        </button>
        <button
          type="button"
          onClick={() => toggleCompareNode(node.id)}
          disabled={isRoot || node.status !== "completed"}
          className={
            inCompare
              ? "rounded-full border border-[color:var(--color-accent)] bg-accent-soft px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-[color:var(--color-accent-strong)]"
              : "rounded-full border border-line bg-paper px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-ink hover:border-line-strong disabled:border-line/50 disabled:text-ink-soft disabled:cursor-not-allowed disabled:hover:border-line/50"
          }
        >
          {inCompare ? "In compare" : "Add to compare"}
        </button>
        <button
          type="button"
          onClick={() => void deleteBranch(node.id)}
          disabled={!canDelete}
          className="ml-auto rounded-full px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-ink-muted hover:text-[color:var(--color-danger)] disabled:text-ink-soft disabled:cursor-not-allowed disabled:hover:text-ink-soft"
        >
          Delete
        </button>
      </div>

      {/* Underlined tabs */}
      <div className="mt-5 flex items-center gap-1 border-b border-line">
        {(["overview", "logs", "diff"] as Tab[]).map((t) => {
          const active = tab === t;
          return (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={`relative px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.16em] transition ${
                active ? "text-ink" : "text-ink-muted hover:text-ink"
              }`}
            >
              {t === "logs"
                ? `Logs${logs.length ? ` (${logs.length})` : ""}`
                : t.charAt(0).toUpperCase() + t.slice(1)}
              {active && (
                <span className="absolute -bottom-px left-0 right-0 h-px bg-ink" aria-hidden />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab body — flex-1 to absorb middle space; bottom tiles pinned with mt-auto */}
      <div className="mt-4 flex flex-1 flex-col">
        {tab === "overview" ? (
          <div className="flex flex-1 flex-col">
            <div className="space-y-4">
              <p className="text-[13px] leading-6 text-ink">
                {node.prompt ?? node.summary ?? "Prepared for a new implementation path."}
              </p>
              {evalReady ? (
                <div className="rounded-lg border border-line bg-paper p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-ink-soft">
                    Eval
                  </p>
                  <p className="mt-1 font-mono text-[12.5px] text-ink">
                    <span className="text-[color:var(--color-success)]">
                      ✓ {node.eval_passed} passed
                    </span>
                    {node.eval_failed && node.eval_failed > 0 ? (
                      <span className="ml-2 text-[color:var(--color-danger)]">
                        ✗ {node.eval_failed} failed
                      </span>
                    ) : null}
                  </p>
                  {node.eval_summary ? (
                    <p className="mt-1 text-[12px] text-ink-muted">{node.eval_summary}</p>
                  ) : null}
                </div>
              ) : null}
            </div>
            {/* Bottom tiles — pinned to drawer bottom */}
            <div className="mt-auto grid gap-2 pt-6 sm:grid-cols-2">
              <Tile label="Worktree" value={compactPath(node.worktree_path)} />
              <Tile label="Last update" value={formatTimestamp(node.updated_at)} />
            </div>
          </div>
        ) : null}

        {tab === "logs" ? <AgentLogPanel entries={logs} /> : null}
        {tab === "diff" ? <DiffPanel nodeId={node.id} /> : null}
      </div>
    </aside>
  );
}

function Tile({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-lg border border-line bg-paper p-3">
      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-ink-soft">
        {label}
      </p>
      <p className="mt-1 truncate font-mono text-[12px] leading-5 text-ink" title={value}>
        {value}
      </p>
    </div>
  );
}
