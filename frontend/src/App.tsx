import { startTransition, useEffect } from "react";
import { GraphView } from "./components/GraphView";
import { StatusBadge } from "./components/StatusBadge";
import { Toolbar } from "./components/Toolbar";
import { useGraphStore } from "./store/graphStore";

function formatTimestamp(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Awaiting activity";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function compactPath(path: string) {
  const segments = path.split(/[/\\]+/).filter(Boolean);

  if (segments.length <= 3) {
    return path;
  }

  return `.../${segments.slice(-3).join("/")}`;
}

export function App() {
  const { graph, selectedNodeId, isLoading, loadGraph, selectNode, addDraftBranch } =
    useGraphStore();
  const selectedNode =
    graph.nodes.find((node) => node.id === selectedNodeId) ?? graph.nodes[0];
  const activeNodeCount = graph.nodes.filter(
    (node) => node.status === "queued" || node.status === "running",
  ).length;
  const completedNodeCount = graph.nodes.filter(
    (node) => node.status === "completed" || node.status === "merged",
  ).length;

  useEffect(() => {
    startTransition(() => {
      void loadGraph();
    });
  }, [loadGraph]);

  return (
    <div className="min-h-screen bg-[#050607] text-white">
      <main className="relative min-h-screen overflow-hidden">
        <GraphView
          graph={graph}
          selectedNodeId={selectedNodeId}
          onSelectNode={selectNode}
        />

        <div className="pointer-events-none absolute inset-x-0 top-0 z-20 p-4 sm:p-6">
          <div className="flex items-start justify-between gap-3">
            <div className="pointer-events-auto max-w-xl">
              <Toolbar baseBranch={graph.base_branch} onCreateBranch={addDraftBranch} />
            </div>
            <div className="pointer-events-auto hidden items-center gap-2 md:flex">
              <div className="rounded-full border border-white/10 bg-black/35 px-3 py-2 text-[11px] font-medium text-white/70 backdrop-blur-xl">
                {graph.nodes.length} branches in view
              </div>
              <div className="rounded-full border border-white/10 bg-black/35 px-3 py-2 text-[11px] font-medium text-white/70 backdrop-blur-xl">
                {activeNodeCount} active
              </div>
              <div className="rounded-full border border-white/10 bg-black/35 px-3 py-2 text-[11px] font-medium text-white/70 backdrop-blur-xl">
                {completedNodeCount} ready to compare
              </div>
            </div>
          </div>
        </div>

        <div className="pointer-events-none absolute inset-x-0 bottom-0 z-20 p-4 sm:p-6">
          <div className="flex justify-end">
            <aside className="pointer-events-auto w-full max-w-[22rem] rounded-[2rem] border border-white/10 bg-[#0d0f11]/88 p-5 shadow-[0_24px_80px_rgba(0,0,0,0.48)] backdrop-blur-2xl">
              <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-white/35">
                Selected branch
              </p>
              {selectedNode ? (
                <div className="mt-4 space-y-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <h1 className="font-display text-[1.7rem] font-semibold tracking-[-0.03em] text-white">
                        {selectedNode.label}
                      </h1>
                      <p className="mt-1 truncate text-sm text-white/45">
                        {selectedNode.branch_name}
                      </p>
                    </div>
                    <StatusBadge status={selectedNode.status} />
                  </div>

                  <p className="text-sm leading-6 text-white/72">
                    {selectedNode.prompt ??
                      selectedNode.summary ??
                      "Prepared for a new implementation path from the base branch."}
                  </p>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-3">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-white/35">
                        Worktree
                      </p>
                      <p className="mt-2 break-all text-sm leading-6 text-white/72">
                        {compactPath(selectedNode.worktree_path)}
                      </p>
                    </div>
                    <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-3">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-white/35">
                        Last update
                      </p>
                      <p className="mt-2 text-sm leading-6 text-white/72">
                        {formatTimestamp(selectedNode.updated_at)}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-white/8 bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgba(255,255,255,0.02))] p-4">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-white/35">
                      Why this view
                    </p>
                    <p className="mt-2 text-sm leading-6 text-white/62">
                      The canvas stays primary while branch detail appears only when it helps
                      decide between implementation paths.
                    </p>
                    <p className="mt-3 text-sm leading-6 text-white/72">
                      {isLoading
                        ? "Syncing the latest graph snapshot from the backend."
                        : selectedNode.summary ??
                          "Node contract is live and ready for worktree lifecycle, logs, diffs, and merge flow."}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="mt-4 text-sm text-white/55">No branch selected.</p>
              )}
            </aside>
          </div>
        </div>
      </main>
    </div>
  );
}
