import { useEffect } from "react";
import { useGraphStore } from "../store/graphStore";
import { StatusBadge } from "./StatusBadge";
import { StrategyChip } from "./StrategyBadge";
import { UnifiedDiffView } from "./UnifiedDiffView";
import type { GraphNode } from "../types";

export function ComparePanel() {
  const compare = useGraphStore((s) => s.compare);
  const close = useGraphStore((s) => s.closeCompare);
  const graph = useGraphStore((s) => s.graph);
  const diffs = useGraphStore((s) => s.diffs);
  const refreshDiff = useGraphStore((s) => s.refreshDiff);
  const mergeBranch = useGraphStore((s) => s.mergeBranch);
  const toggleCompareNode = useGraphStore((s) => s.toggleCompareNode);

  const nodes = compare.nodeIds
    .map((id) => graph.nodes.find((n) => n.id === id))
    .filter((n): n is GraphNode => Boolean(n));

  useEffect(() => {
    if (!compare.open) return;
    for (const id of compare.nodeIds) {
      if (!diffs[id]) void refreshDiff(id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [compare.open, compare.nodeIds]);

  useEffect(() => {
    if (!compare.open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [compare.open, close]);

  if (!compare.open) return null;

  return (
    <div className="fixed inset-0 z-40 flex flex-col bg-paper" role="dialog" aria-modal="true" aria-label="Compare branches">
      <header className="hairline-bottom flex items-center justify-between bg-surface px-6 py-4">
        <div>
          <p className="font-mono text-[10px] font-medium uppercase tracking-eyebrow text-accent">
            Compare
          </p>
          <h2 className="mt-0.5 font-display text-2xl font-medium tracking-[-0.025em] text-ink">
            {nodes.length} candidate{nodes.length === 1 ? "" : "s"}
          </h2>
        </div>
        <button
          type="button"
          onClick={close}
          className="rounded-sm border border-line bg-surface px-3 py-1.5 font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-muted hover:bg-paper-deep hover:text-ink"
        >
          Close · Esc
        </button>
      </header>

      <div className="grid flex-1 grid-cols-1 gap-4 overflow-auto p-6 lg:grid-cols-2 xl:grid-cols-3">
        {nodes.map((node) => (
          <CandidateCard
            key={node.id}
            node={node}
            cached={diffs[node.id]}
            onMerge={() => void mergeBranch(node.id)}
            onRemove={() => toggleCompareNode(node.id)}
          />
        ))}
      </div>
    </div>
  );
}

function CandidateCard({
  node,
  cached,
  onMerge,
  onRemove,
}: {
  node: GraphNode;
  cached: { diff: string; has_changes: boolean } | undefined;
  onMerge: () => void;
  onRemove: () => void;
}) {
  const stats = computeStats(cached?.diff);
  const evalReady = node.eval_passed !== null && node.eval_passed !== undefined;

  return (
    <div className="flex min-h-0 flex-col rounded-md border border-line bg-surface shadow-panel">
      <div className="hairline-bottom flex items-start justify-between gap-3 p-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="truncate font-display text-lg font-medium text-ink">{node.label}</h3>
            {node.strategy ? <StrategyChip strategy={node.strategy} /> : null}
          </div>
          <p className="mt-0.5 truncate font-mono text-[11px] text-ink-muted">{node.branch_name}</p>
        </div>
        <StatusBadge status={node.status} />
      </div>

      <div className="grid grid-cols-3 gap-3 border-b border-line bg-paper-deep px-4 py-2.5 font-mono text-[11px] tabular-num">
        <Signal
          label="Tests"
          value={
            evalReady
              ? `${node.eval_passed}/${(node.eval_passed ?? 0) + (node.eval_failed ?? 0)}`
              : "—"
          }
          tone={
            evalReady && (node.eval_failed ?? 0) === 0
              ? "text-[color:var(--color-success)]"
              : evalReady
              ? "text-danger"
              : "text-ink-soft"
          }
        />
        <Signal
          label="+ / −"
          value={cached?.has_changes ? `+${stats.added} / −${stats.removed}` : "—"}
        />
        <Signal label="Files" value={cached?.has_changes ? String(stats.files) : "—"} />
      </div>

      <div className="min-h-0 flex-1 overflow-auto p-3">
        {cached?.has_changes ? (
          <UnifiedDiffView diff={cached.diff} />
        ) : cached ? (
          <p className="p-3 font-mono text-[12px] text-ink-soft">No changes.</p>
        ) : (
          <p className="p-3 font-mono text-[12px] text-ink-soft">Loading diff…</p>
        )}
      </div>

      <div className="flex items-center justify-end gap-2 border-t border-line bg-paper-deep p-3">
        <button
          type="button"
          onClick={onRemove}
          className="rounded-sm border border-line bg-surface px-2.5 py-1 font-mono text-[10.5px] font-medium uppercase tracking-eyebrow text-ink-muted hover:bg-paper-deep hover:text-ink"
        >
          Remove
        </button>
        <button
          type="button"
          onClick={onMerge}
          disabled={node.status !== "completed"}
          className="rounded-sm border border-[color:var(--color-accent)] bg-accent px-3 py-1 font-mono text-[10.5px] font-medium uppercase tracking-eyebrow text-white transition hover:bg-accent-strong disabled:opacity-40"
        >
          Pick this one
        </button>
      </div>
    </div>
  );
}

function Signal({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-[9.5px] uppercase tracking-eyebrow text-ink-soft">{label}</span>
      <span className={`mt-0.5 ${tone ?? "text-ink"}`}>{value}</span>
    </div>
  );
}

function computeStats(diff: string | undefined) {
  if (!diff) return { added: 0, removed: 0, files: 0 };
  let added = 0;
  let removed = 0;
  const files = new Set<string>();
  for (const line of diff.split("\n")) {
    if (line.startsWith("diff --git ")) {
      const parts = line.split(" b/");
      if (parts.length === 2) files.add(parts[1]);
      continue;
    }
    if (line.startsWith("+++") || line.startsWith("---")) continue;
    if (line.startsWith("+")) added += 1;
    else if (line.startsWith("-")) removed += 1;
  }
  return { added, removed, files: files.size };
}
