import { useEffect } from "react";
import { useGraphStore } from "../store/graphStore";
import { StatusBadge } from "./StatusBadge";
import { UnifiedDiffView } from "./UnifiedDiffView";

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
    .filter((n): n is NonNullable<typeof n> => Boolean(n));

  // Trigger diff fetches only when the panel opens or its node set changes.
  // `nodes` is recomputed each render (fresh array ref) and `diffs` mutates
  // when refreshDiff completes — including either in deps would loop the
  // effect. The fetch itself is idempotent because refreshDiff sets the entry.
  useEffect(() => {
    if (!compare.open) return;
    for (const id of compare.nodeIds) {
      if (!diffs[id]) void refreshDiff(id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [compare.open, compare.nodeIds]);

  if (!compare.open) return null;

  return (
    <div className="fixed inset-0 z-40 flex flex-col bg-black/85 backdrop-blur-md">
      <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-white/40">
            Compare
          </p>
          <h2 className="font-display text-2xl font-semibold tracking-[-0.03em] text-white">
            {nodes.length} candidate{nodes.length === 1 ? "" : "s"}
          </h2>
        </div>
        <button
          type="button"
          onClick={close}
          className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-white/70 hover:bg-white/[0.08]"
        >
          Close
        </button>
      </div>

      <div className="grid flex-1 grid-cols-1 gap-4 overflow-auto p-6 lg:grid-cols-2 xl:grid-cols-3">
        {nodes.map((node) => {
          const cached = diffs[node.id];
          return (
            <div
              key={node.id}
              className="flex flex-col rounded-2xl border border-white/10 bg-[#0d0f11]/80 p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-display text-lg font-semibold text-white">
                    {node.label}
                  </h3>
                  <p className="mt-1 text-xs text-white/50">{node.branch_name}</p>
                </div>
                <StatusBadge status={node.status} />
              </div>

              <div className="mt-3 max-h-[420px] flex-1 overflow-auto">
                {cached?.has_changes ? (
                  <UnifiedDiffView diff={cached.diff} />
                ) : cached ? (
                  <p className="p-3 text-sm text-white/45">No changes.</p>
                ) : (
                  <p className="p-3 text-sm text-white/45">Loading diff…</p>
                )}
              </div>

              <div className="mt-3 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => toggleCompareNode(node.id)}
                  className="rounded-full border border-white/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] text-white/70 hover:bg-white/[0.08]"
                >
                  Remove
                </button>
                <button
                  type="button"
                  onClick={() => void mergeBranch(node.id)}
                  disabled={node.status !== "completed"}
                  className="rounded-full border border-emerald-400/40 bg-emerald-400/15 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-100 hover:bg-emerald-400/25 disabled:opacity-40"
                >
                  Pick winner
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
