import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import type { AgentLogEntry, GraphNode, NodeStrategy } from "../types";
import { useGraphStore } from "../store/graphStore";
import { StatusBadge } from "./StatusBadge";
import { StrategyAvatar } from "./StrategyBadge";

export type WorktreeFlowNode = Node<GraphNode, "worktree">;

const EMPTY_LOGS: AgentLogEntry[] = [];

const ROOT_DESCRIPTION = "Clean demo baseline. All agent approaches branch from here.";

const STRATEGY_DESCRIPTIONS: Record<NodeStrategy, string> = {
  route_local: "Route-local: checks the login limit inside the POST /api/login flow.",
  dependency: "Dependency: enforces the limit with a FastAPI Depends hook.",
  middleware: "Middleware: intercepts POST /api/login before the handler runs.",
};

function lastToolUse(logs: AgentLogEntry[]): AgentLogEntry | null {
  for (let i = logs.length - 1; i >= 0; i--) {
    if (logs[i].type === "tool_use") return logs[i];
  }
  return null;
}

function summarizeTool(entry: AgentLogEntry): string {
  const name = entry.tool_name ?? "tool";
  const input = entry.tool_input ?? {};
  const target =
    (typeof input.file_path === "string" && input.file_path) ||
    (typeof input.path === "string" && input.path) ||
    (typeof input.command === "string" && input.command) ||
    (typeof input.pattern === "string" && input.pattern) ||
    "";
  if (!target) return name;
  const segments = target.split(/[/\\]+/).filter(Boolean);
  const short = segments.length <= 2 ? target : segments.slice(-2).join("/");
  return `${name} · ${short}`;
}

export function WorktreeNode({ data, selected }: NodeProps<WorktreeFlowNode>) {
  const runBranch = useGraphStore((s) => s.runBranch);
  const logs = useGraphStore((s) => s.agentLogs[data.id] ?? EMPTY_LOGS);
  const isRoot = data.parent_id === null;
  const isRunning = data.status === "running";
  const canRun = !isRoot && (data.status === "idle" || data.status === "failed");

  const placeholder = isRoot
    ? ROOT_DESCRIPTION
    : "Awaiting prompt — define an implementation path.";
  const description = data.strategy
    ? STRATEGY_DESCRIPTIONS[data.strategy]
    : data.prompt ?? placeholder;

  const ticker = isRunning ? lastToolUse(logs) : null;
  const tickerLabel = ticker ? summarizeTool(ticker) : isRunning ? "Working…" : null;
  const evalReady =
    data.eval_passed !== null && data.eval_passed !== undefined;

  const surfaceClass = selected
    ? "bg-paper-deep border-line-strong"
    : isRoot
      ? "bg-paper-deep border-line hover:border-line-strong"
      : "bg-surface-raised border-line hover:border-line-strong hover:shadow-panel-lg";

  const selectedRing = selected
    ? "shadow-[0_0_0_1.5px_rgba(216,73,46,0.22),0_1px_0_rgba(26,26,29,0.05),0_12px_32px_rgba(26,26,29,0.08)]"
    : "shadow-panel";

  return (
    <div
      className={`relative w-[300px] overflow-hidden rounded-2xl border transition duration-200 ${surfaceClass} ${selectedRing}`}
    >
      <div
        className={`h-[3px] w-full ${
          isRunning
            ? "bg-accent accent-pulse"
            : data.status === "completed"
            ? "bg-success"
            : data.status === "merged"
            ? "bg-success"
            : data.status === "failed"
            ? "bg-danger"
            : "bg-line-strong"
        }`}
      />

      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border !border-line-strong !bg-surface"
      />

      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            {data.strategy ? <StrategyAvatar strategy={data.strategy} /> : null}
            <span className="truncate font-mono text-[11px] text-ink-muted">
              {data.branch_name}
            </span>
          </div>
          <StatusBadge status={data.status} />
        </div>

        <p className="mt-3 font-display text-[1.1rem] font-medium leading-tight tracking-[-0.015em] text-ink">
          {data.label}
        </p>

        <p className="mt-1.5 line-clamp-2 text-[12.5px] leading-5 text-ink-muted">
          {description}
        </p>

        {tickerLabel ? (
          <p className="mt-3 truncate font-mono text-[11px] text-accent">
            ↻ {tickerLabel}
          </p>
        ) : null}

        {evalReady ? (
          <div className="mt-3 flex items-center gap-2 font-mono text-[11px] tabular-num text-ink-muted">
            <span className="text-[color:var(--color-success)]">
              ✓ {data.eval_passed} passed
            </span>
            {data.eval_failed && data.eval_failed > 0 ? (
              <span className="text-danger">✗ {data.eval_failed} failed</span>
            ) : null}
          </div>
        ) : null}

        <div className="mt-4 flex items-center justify-between gap-3">
          <span className="font-mono text-[10.5px] tabular-num text-ink-soft">
            {new Date(data.updated_at).toLocaleTimeString([], {
              hour: "numeric",
              minute: "2-digit",
            })}
          </span>
          {canRun ? (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                void runBranch(data.id);
              }}
              className="rounded-sm border border-[color:var(--color-accent)] bg-accent-soft px-2.5 py-0.5 font-mono text-[10.5px] font-medium uppercase tracking-eyebrow text-accent-strong transition hover:bg-accent hover:text-white"
            >
              Run
            </button>
          ) : null}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border !border-line-strong !bg-surface"
      />
    </div>
  );
}
