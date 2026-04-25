import { useState } from "react";
import { AgentLogPanel } from "./AgentLogPanel";
import { DiffPanel } from "./DiffPanel";
import { NodeSummaryCard } from "./NodeSummaryCard";
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

export function DetailPanel({ node }: { node: GraphNode }) {
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
    <aside className="pointer-events-auto w-full max-w-[26rem] rounded-lg border border-line bg-surface p-5 shadow-panel-lg">
      <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-eyebrow text-ink-soft">
        <span>Selected branch</span>
        {node.strategy ? <StrategyChip strategy={node.strategy} /> : null}
      </div>

      <div className="mt-3 flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="font-display text-[1.7rem] font-medium leading-tight tracking-[-0.025em] text-ink">
            {node.label}
          </h1>
          <p className="mt-0.5 truncate font-mono text-[12px] text-ink-muted">{node.branch_name}</p>
        </div>
        <StatusBadge status={node.status} />
      </div>

      <div className="mt-4 flex flex-wrap gap-1.5">
        <ActionButton kind="primary" onClick={() => void runBranch(node.id)} disabled={!canRun}>
          Run
        </ActionButton>
        <ActionButton kind="success" onClick={() => void mergeBranch(node.id)} disabled={!canMerge}>
          Merge
        </ActionButton>
        <ActionButton
          kind={inCompare ? "active" : "default"}
          onClick={() => toggleCompareNode(node.id)}
          disabled={isRoot || node.status !== "completed"}
        >
          {inCompare ? "In compare" : "Add to compare"}
        </ActionButton>
        <ActionButton kind="danger" onClick={() => void deleteBranch(node.id)} disabled={!canDelete}>
          Delete
        </ActionButton>
      </div>

      <div className="mt-5 inline-flex rounded-sm border border-line bg-paper-deep p-0.5">
        {(["overview", "logs", "diff"] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded-sm px-3 py-1 font-mono text-[10.5px] font-medium uppercase tracking-eyebrow transition ${
              tab === t ? "bg-surface text-ink shadow-panel" : "text-ink-muted hover:text-ink"
            }`}
          >
            {t === "logs" ? `Logs${logs.length ? ` ${logs.length}` : ""}` : t}
          </button>
        ))}
      </div>

      <div className="mt-4">
        {tab === "overview" ? (
          <div className="space-y-4">
            <p className="text-[13px] leading-6 text-ink">
              {node.prompt ?? node.summary ?? "Prepared for a new implementation path."}
            </p>
            {!isRoot ? <NodeSummaryCard node={node} /> : null}
            <div className="grid gap-2 sm:grid-cols-2">
              <Tile label="Worktree" value={compactPath(node.worktree_path)} />
              <Tile label="Last update" value={formatTimestamp(node.updated_at)} />
            </div>
            {evalReady ? (
              <div className="rounded-sm border border-line bg-paper-deep p-3">
                <p className="font-mono text-[10px] uppercase tracking-eyebrow text-ink-soft">
                  Eval
                </p>
                <p className="mt-1 font-mono text-[12.5px] text-ink">
                  <span className="text-[color:var(--color-success)]">
                    ✓ {node.eval_passed} passed
                  </span>
                  {node.eval_failed && node.eval_failed > 0 ? (
                    <span className="ml-2 text-danger">✗ {node.eval_failed} failed</span>
                  ) : null}
                </p>
                {node.eval_summary ? (
                  <p className="mt-1 text-[12px] text-ink-muted">{node.eval_summary}</p>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : null}

        {tab === "logs" ? <AgentLogPanel entries={logs} /> : null}
        {tab === "diff" ? <DiffPanel nodeId={node.id} /> : null}
      </div>
    </aside>
  );
}

function ActionButton({
  kind,
  onClick,
  disabled,
  children,
}: {
  kind: "primary" | "success" | "danger" | "active" | "default";
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  const tone = {
    primary: "border-[color:var(--color-accent)] bg-accent-soft text-accent-strong hover:bg-accent hover:text-white",
    success: "border-[color:var(--color-success)]/30 bg-success-soft text-[color:var(--color-success)] hover:bg-[color:var(--color-success)] hover:text-white",
    danger: "border-[color:var(--color-danger)]/30 bg-danger-soft text-danger hover:bg-[color:var(--color-danger)] hover:text-white",
    active: "border-[color:var(--color-accent)] bg-accent text-white",
    default: "border-line bg-surface text-ink-muted hover:bg-paper-deep hover:text-ink",
  }[kind];
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`rounded-sm border px-2.5 py-1 font-mono text-[10.5px] font-medium uppercase tracking-eyebrow transition disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-current ${tone}`}
    >
      {children}
    </button>
  );
}

function Tile({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-sm border border-line bg-paper-deep p-3">
      <p className="font-mono text-[10px] uppercase tracking-eyebrow text-ink-soft">
        {label}
      </p>
      <p className="mt-1 truncate text-[13px] leading-5 text-ink" title={value}>
        {value}
      </p>
    </div>
  );
}
