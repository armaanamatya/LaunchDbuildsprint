import type { GraphNode, SummaryRecommendation, SummaryRisk } from "../types";

const RISK_TONE: Record<SummaryRisk, string> = {
  low: "border-[color:var(--color-success)]/30 bg-success-soft text-[color:var(--color-success)]",
  medium: "border-[color:var(--color-accent)]/30 bg-accent-soft text-accent-strong",
  high: "border-[color:var(--color-danger)]/30 bg-danger-soft text-danger",
  unknown: "border-line bg-paper-deep text-ink-muted",
};

const REC_LABEL: Record<SummaryRecommendation, string> = {
  merge_candidate: "Merge candidate",
  needs_review: "Needs review",
  do_not_merge: "Do not merge",
};

const REC_TONE: Record<SummaryRecommendation, string> = {
  merge_candidate:
    "border-[color:var(--color-success)]/30 bg-success-soft text-[color:var(--color-success)]",
  needs_review: "border-line bg-paper-deep text-ink",
  do_not_merge:
    "border-[color:var(--color-danger)]/30 bg-danger-soft text-danger",
};

const MAX_VISIBLE_FILES = 6;

type NodeSummaryCardProps = {
  node: GraphNode;
  compact?: boolean;
};

function PendingState({ node }: { node: GraphNode }) {
  let message: string;
  switch (node.status) {
    case "running":
    case "queued":
      message = "Summary will appear after the agent finishes.";
      break;
    case "failed":
      message = "No summary generated. Check logs and diff.";
      break;
    default:
      message = "Run this branch to generate a decision summary.";
  }
  return (
    <div className="rounded-sm border border-line bg-paper-deep p-3">
      <p className="font-mono text-[10px] uppercase tracking-eyebrow text-ink-soft">
        Decision summary
      </p>
      <p className="mt-1 text-[12.5px] text-ink-muted">{message}</p>
    </div>
  );
}

export function NodeSummaryCard({ node, compact = false }: NodeSummaryCardProps) {
  const summary = node.decision_summary;
  if (!summary) return <PendingState node={node} />;

  const visibleFiles = summary.changed_files.slice(0, MAX_VISIBLE_FILES);
  const overflow = summary.changed_files.length - visibleFiles.length;
  const diffLine = `${summary.files_changed} file${summary.files_changed === 1 ? "" : "s"} · +${summary.insertions} −${summary.deletions}`;

  return (
    <div className="rounded-sm border border-line bg-paper-deep p-3">
      <div className="flex items-start justify-between gap-2">
        <p className="font-mono text-[10px] uppercase tracking-eyebrow text-ink-soft">
          Decision summary
        </p>
        <div className="flex shrink-0 gap-1">
          <span
            className={`inline-flex items-center rounded-full border px-2 py-0.5 font-mono text-[9.5px] font-semibold uppercase tracking-eyebrow ${RISK_TONE[summary.risk]}`}
            title={summary.risk_reason}
          >
            {summary.risk} risk
          </span>
          <span
            className={`inline-flex items-center rounded-full border px-2 py-0.5 font-mono text-[9.5px] font-semibold uppercase tracking-eyebrow ${REC_TONE[summary.recommendation]}`}
          >
            {REC_LABEL[summary.recommendation]}
          </span>
        </div>
      </div>

      <p className="mt-2 text-[13px] leading-5 text-ink">{summary.headline}</p>
      <p className="mt-0.5 font-mono text-[11px] text-ink-muted">
        {summary.approach} · {diffLine}
      </p>

      {!compact && summary.test_summary ? (
        <p className="mt-1.5 font-mono text-[11px] text-ink-muted">
          Tests: {summary.test_summary}
        </p>
      ) : null}

      {!compact && summary.review_focus.length > 0 ? (
        <ul className="mt-2 space-y-0.5 text-[12px] leading-5 text-ink">
          {summary.review_focus.map((bullet) => (
            <li key={bullet} className="flex gap-1.5">
              <span className="text-ink-soft">•</span>
              <span>{bullet}</span>
            </li>
          ))}
        </ul>
      ) : null}

      {!compact && visibleFiles.length > 0 ? (
        <div className="mt-2">
          <p className="font-mono text-[10px] uppercase tracking-eyebrow text-ink-soft">
            Changed files
          </p>
          <ul className="mt-1 space-y-0.5 font-mono text-[11px] text-ink-muted">
            {visibleFiles.map((path) => (
              <li key={path} className="truncate" title={path}>
                {path}
              </li>
            ))}
            {overflow > 0 ? (
              <li className="text-ink-soft">+{overflow} more</li>
            ) : null}
          </ul>
        </div>
      ) : null}

      <p className="mt-2 font-mono text-[10px] text-ink-soft" title={summary.risk_reason}>
        Why {summary.risk}: {summary.risk_reason}
      </p>
    </div>
  );
}
