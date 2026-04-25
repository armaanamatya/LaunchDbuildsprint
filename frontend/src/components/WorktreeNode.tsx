import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import type { GraphNode } from "../types";
import { StatusBadge } from "./StatusBadge";

export type WorktreeFlowNode = Node<GraphNode, "worktree">;

function compactPath(path: string) {
  const segments = path.split(/[/\\]+/).filter(Boolean);

  if (segments.length <= 2) {
    return path;
  }

  return `.../${segments.slice(-2).join("/")}`;
}

export function WorktreeNode({ data, selected }: NodeProps<WorktreeFlowNode>) {
  return (
    <div
      className={`w-[340px] rounded-[1.35rem] border bg-[#151617]/96 p-5 shadow-[0_18px_55px_rgba(0,0,0,0.45)] backdrop-blur-xl transition duration-200 ${
        selected
          ? "border-amber-300/45 bg-[#191a1c]/98 shadow-[0_0_0_1px_rgba(251,191,36,0.24),0_22px_70px_rgba(0,0,0,0.58)]"
          : "border-white/8 hover:border-white/14"
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2.5 !w-2.5 !border !border-white/20 !bg-[#0d0f11]"
      />

      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[10px] font-medium text-white/70">
              {data.branch_name}
            </span>
            <span className="rounded-full border border-white/8 px-2 py-1 text-[10px] font-medium text-white/40">
              path
            </span>
          </div>
        </div>
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

        <p className="min-h-[72px] text-[13px] leading-6 text-white/62">
          {data.summary ?? "No execution summary yet. Launch this branch to inspect progress and compare the resulting diff."}
        </p>
      </div>

      <div className="mt-5 flex items-center justify-between">
        <div className="text-[11px] uppercase tracking-[0.22em] text-white/30">
          {data.parent_id ? "Derived branch" : "Base workspace"}
        </div>
        <div className="flex items-center gap-2 text-white/40">
          <span className="rounded-full border border-white/8 px-2 py-1 text-[11px]">link</span>
          <span className="rounded-full border border-white/8 px-2 py-1 text-[11px]">diff</span>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2.5 !w-2.5 !border !border-white/20 !bg-[#0d0f11]"
      />
    </div>
  );
}
