import { useState } from "react";
import { AgentLogPanel } from "./AgentLogPanel";
import { DiffPanel } from "./DiffPanel";
import { StatusBadge } from "./StatusBadge";
import { useGraphStore } from "../store/graphStore";
import type { AgentLogEntry, GraphNode } from "../types";

type Tab = "overview" | "logs" | "diff";

// Stable empty array. Returning `?? []` from a Zustand selector creates a
// fresh array reference each call, which useSyncExternalStore reads as a
// changed snapshot and triggers an infinite re-render loop.
const EMPTY_LOGS: AgentLogEntry[] = [];

function compactPath(path: string) {
  const segments = path.split(/[/\\]+/).filter(Boolean);
  return segments.length <= 3 ? path : `.../${segments.slice(-3).join("/")}`;
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
  const canRun = !isRoot && (node.status === "idle" || node.status === "queued");
  const canMerge = node.status === "completed";
  const canDelete = !isRoot && node.status !== "running";
  const inCompare = compare.nodeIds.includes(node.id);

  return (
    <aside className="pointer-events-auto w-full max-w-[26rem] rounded-[2rem] border border-white/10 bg-[#0d0f11]/88 p-5 shadow-[0_24px_80px_rgba(0,0,0,0.48)] backdrop-blur-2xl">
      <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-white/35">
        Selected branch
      </p>

      <div className="mt-4 flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="font-display text-[1.7rem] font-semibold tracking-[-0.03em] text-white">
            {node.label}
          </h1>
          <p className="mt-1 truncate text-sm text-white/45">{node.branch_name}</p>
        </div>
        <StatusBadge status={node.status} />
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => void runBranch(node.id)}
          disabled={!canRun}
          className="rounded-full border border-sky-400/30 bg-sky-400/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] text-sky-100 hover:bg-sky-400/20 disabled:opacity-40"
        >
          Run
        </button>
        <button
          type="button"
          onClick={() => void mergeBranch(node.id)}
          disabled={!canMerge}
          className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-100 hover:bg-emerald-400/20 disabled:opacity-40"
        >
          Merge
        </button>
        <button
          type="button"
          onClick={() => toggleCompareNode(node.id)}
          disabled={isRoot || node.status !== "completed"}
          className={`rounded-full border px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] disabled:opacity-40 ${
            inCompare
              ? "border-amber-400/40 bg-amber-400/15 text-amber-100"
              : "border-white/10 bg-white/[0.04] text-white/70 hover:bg-white/[0.08]"
          }`}
        >
          {inCompare ? "In compare" : "Add to compare"}
        </button>
        <button
          type="button"
          onClick={() => void deleteBranch(node.id)}
          disabled={!canDelete}
          className="rounded-full border border-rose-400/30 bg-rose-400/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] text-rose-100 hover:bg-rose-400/20 disabled:opacity-40"
        >
          Delete
        </button>
      </div>

      <div className="mt-5 flex gap-1 rounded-full border border-white/8 bg-white/[0.03] p-1">
        {(["overview", "logs", "diff"] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`flex-1 rounded-full px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.18em] ${
              tab === t ? "bg-white/10 text-white" : "text-white/55 hover:text-white/80"
            }`}
          >
            {t === "logs" ? `Logs${logs.length ? ` (${logs.length})` : ""}` : t}
          </button>
        ))}
      </div>

      <div className="mt-4">
        {tab === "overview" ? (
          <div className="space-y-4">
            <p className="text-sm leading-6 text-white/72">
              {node.prompt ?? node.summary ?? "Prepared for a new implementation path."}
            </p>
            <div className="grid gap-3 sm:grid-cols-2">
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
    <div className="min-w-0 rounded-2xl border border-white/8 bg-white/[0.03] p-3">
      <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-white/35">
        {label}
      </p>
      <p
        className="mt-2 truncate text-sm leading-6 text-white/72"
        title={value}
      >
        {value}
      </p>
    </div>
  );
}
