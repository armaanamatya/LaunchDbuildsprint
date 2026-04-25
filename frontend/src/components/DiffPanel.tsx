import { useEffect } from "react";
import { UnifiedDiffView } from "./UnifiedDiffView";
import { useGraphStore } from "../store/graphStore";

type Props = { nodeId: string };

export function DiffPanel({ nodeId }: Props) {
  const diff = useGraphStore((s) => s.diffs[nodeId] ?? null);
  const refreshDiff = useGraphStore((s) => s.refreshDiff);

  useEffect(() => {
    if (!diff && nodeId !== "root") {
      void refreshDiff(nodeId);
    }
  }, [nodeId, diff, refreshDiff]);

  if (nodeId === "root") {
    return <p className="text-sm text-white/45">Root branch — no diff.</p>;
  }

  if (!diff) {
    return <p className="text-sm text-white/45">Loading diff…</p>;
  }

  if (!diff.has_changes) {
    return <p className="text-sm text-white/45">No changes yet on this branch.</p>;
  }

  return (
    <div className="max-h-[420px]">
      <UnifiedDiffView diff={diff.diff} />
    </div>
  );
}
