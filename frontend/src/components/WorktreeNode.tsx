import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import type { GraphNode } from "../types";
import { useGraphStore } from "../store/graphStore";
import { StatusBadge } from "./StatusBadge";

export type WorktreeFlowNode = Node<GraphNode, "worktree">;

function compactPath(path: string) {
  const segments = path.split(/[/\\]+/).filter(Boolean);
  return segments.length <= 2 ? path : `.../${segments.slice(-2).join("/")}`;
}

export function WorktreeNode({ data, selected }: NodeProps<WorktreeFlowNode>) {
  const runBranch = useGraphStore((s) => s.runBranch);
  const isRoot = data.parent_id === null;
  const isRunning = data.status === "running";
  const canRun = !isRoot && (data.status === "idle" || data.status === "queued");

  return (
    <div
      className={`relative w-[340px] rounded-[1.35rem] border bg-[#151617]/96 p-5 shadow-[0_18px_55px_rgba(0,0,0,0.45)] backdrop-blur-xl transition duration-200 ${
        selected
          ? "border-amber-300/45 bg-[#191a1c]/98 shadow-[0_0_0_1px_rgba(251,191,36,0.24),0_22px_70px_rgba(0,0,0,0.58)]"
          : "border-white/8 hover:border-white/14"
      }`}
    >
      {isRunning ? (
        <span className="pointer-events-none absolute inset-0 rounded-[1.35rem] ring-2 ring-sky-400/35 animate-pulse" />
      ) : null}

      <Handle
        type="target"
        position={Position.Top}
        className="!h-2.5 !w-2.5 !border !border-white/20 !bg-[#0d0f11]"
      />

      <div className="flex items-start justify-between gap-3">
        <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[10px] font-medium text-white/70">
          {data.branch_name}
        </span>
        <StatusBadge status={data.status} />
      </div>

      <div className="mt-5 space-y-4">
        <div>
          <p className="font-display text-[1.08rem] font-semibold tracking-[-0.03em] text-white">
            {data.label}
          </p>
          <p className="mt-3 text-sm leading-6 text-white/82">
            {data.prompt ?? "Enter a prompt to explore another implementation path."}
          </p>
        </div>

        <div className="h-px bg-white/8" />

        <div className="rounded-2xl border border-white/8 bg-white/[0.025] px-3 py-2.5 text-[11px] text-white/62">
          <div className="flex items-center justify-between gap-4">
            <span className="truncate">{compactPath(data.worktree_path)}</span>
            <span className="whitespace-nowrap text-white/38">
              {new Date(data.updated_at).toLocaleTimeString([], {
                hour: "numeric",
                minute: "2-digit",
              })}
            </span>
          </div>
        </div>

        <p className="min-h-[48px] text-[13px] leading-6 text-white/62">
          {data.summary ?? "No execution summary yet."}
        </p>
      </div>

      <div className="mt-5 flex items-center justify-between">
        <span className="text-[11px] uppercase tracking-[0.22em] text-white/30">
          {isRoot ? "Base workspace" : "Derived branch"}
        </span>
        {canRun ? (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              void runBranch(data.id);
            }}
            className="rounded-full border border-sky-400/35 bg-sky-400/15 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-100 hover:bg-sky-400/25"
          >
            Run
          </button>
        ) : null}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2.5 !w-2.5 !border !border-white/20 !bg-[#0d0f11]"
      />
    </div>
  );
}
