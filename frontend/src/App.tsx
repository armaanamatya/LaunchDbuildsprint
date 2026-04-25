import { startTransition, useEffect, useMemo, useState } from "react";
import { ComparePanel } from "./components/ComparePanel";
import { ConnectionIndicator } from "./components/ConnectionIndicator";
import { CreateBranchModal } from "./components/CreateBranchModal";
import { DetailPanel } from "./components/DetailPanel";
import { EmptyStateCTA } from "./components/EmptyStateCTA";
import { GraphView } from "./components/GraphView";
import { KeyboardShortcutsOverlay } from "./components/KeyboardShortcutsOverlay";
import { Toolbar } from "./components/Toolbar";
import { ToastHost } from "./components/Toast";
import { useGraphSSE } from "./hooks/useGraphSSE";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";
import { useGraphStore } from "./store/graphStore";

const HERO_PROMPT = `Add rate limiting to POST /api/login in the demo repo.

Requirements:
- Max 5 attempts per IP within a 60-second sliding window.
- Return HTTP 429 with a Retry-After header when exceeded.
- Successful logins must count toward the limit (prevent enumeration).
- The limit applies per-IP regardless of email (prevent email rotation bypass).

Make the four failing tests in tests/test_rate_limit.py pass without breaking tests/test_login.py.`;

export function App() {
  const graph = useGraphStore((s) => s.graph);
  const selectedNodeId = useGraphStore((s) => s.selectedNodeId);
  const loadGraph = useGraphStore((s) => s.loadGraph);
  const selectNode = useGraphStore((s) => s.selectNode);
  const createBranch = useGraphStore((s) => s.createBranch);
  const runBranch = useGraphStore((s) => s.runBranch);
  const mergeBranch = useGraphStore((s) => s.mergeBranch);
  const openCompare = useGraphStore((s) => s.openCompare);
  const resetDemo = useGraphStore((s) => s.resetDemo);

  const [createOpen, setCreateOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);

  const handleCreate = async (label: string, prompt: string) => {
    await createBranch(label, prompt);
  };

  const handleQuickStart = async () => {
    for (let i = 1; i <= 3; i += 1) {
      await createBranch(`Approach ${i}`, HERO_PROMPT);
    }
  };

  useGraphSSE();

  const branchCount = graph.nodes.filter((n) => n.parent_id !== null).length;
  const isEmpty = branchCount === 0;
  const selectedNode = useMemo(
    () => graph.nodes.find((node) => node.id === selectedNodeId) ?? graph.nodes[0],
    [graph.nodes, selectedNodeId],
  );
  const showDetailPanel = !isEmpty && selectedNode && selectedNode.parent_id !== null;
  const activeNodeCount = graph.nodes.filter(
    (node) => node.status === "queued" || node.status === "running",
  ).length;
  const completedNodeCount = graph.nodes.filter(
    (node) => node.status === "completed" || node.status === "merged",
  ).length;
  const branchesLabel = `${branchCount} ${branchCount === 1 ? "branch" : "branches"}`;

  useEffect(() => {
    startTransition(() => {
      void loadGraph();
    });
  }, [loadGraph]);

  useKeyboardShortcuts({
    onNewBranch: () => setCreateOpen(true),
    onRunSelected: () => {
      if (selectedNode && selectedNode.parent_id !== null) {
        void runBranch(selectedNode.id);
      }
    },
    onCompare: () => {
      if (completedNodeCount >= 2) openCompare();
    },
    onMergeSelected: () => {
      if (selectedNode && selectedNode.status === "completed") {
        void mergeBranch(selectedNode.id);
      }
    },
    onShowShortcuts: () => setShortcutsOpen(true),
  });

  return (
    <div className="min-h-screen bg-paper text-ink">
      <main className="relative min-h-screen overflow-hidden">
        {isEmpty ? (
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_28%,rgba(216,73,46,0.06),transparent_55%)]" />
        ) : (
          <GraphView
            graph={graph}
            selectedNodeId={selectedNodeId}
            onSelectNode={selectNode}
          />
        )}

        <div className="pointer-events-none absolute inset-x-0 top-0 z-20 p-4 sm:p-6">
          <div className="flex items-start justify-between gap-3">
            <div className="pointer-events-auto min-w-0 flex-1">
              <Toolbar
                baseBranch={graph.base_branch}
                onOpenCreate={() => setCreateOpen(true)}
                onOpenCompare={openCompare}
                onReset={() => void resetDemo()}
                canCompare={completedNodeCount >= 2}
                completedCount={completedNodeCount}
                showAdvancedActions={!isEmpty}
              />
            </div>
            <div className="pointer-events-auto hidden shrink-0 items-center gap-2 md:flex">
              <ConnectionIndicator />
              {!isEmpty && (
                <>
                  <Stat>{branchesLabel} in view</Stat>
                  <Stat>{activeNodeCount} active</Stat>
                  <Stat>{completedNodeCount} ready to compare</Stat>
                </>
              )}
            </div>
          </div>
        </div>

        {isEmpty && (
          <EmptyStateCTA
            onQuickStart={handleQuickStart}
            onCreate={() => setCreateOpen(true)}
          />
        )}

        {showDetailPanel && selectedNode && (
          <div className="pointer-events-none absolute inset-x-0 bottom-0 z-20 p-4 sm:p-6">
            <div className="flex justify-end">
              <DetailPanel node={selectedNode} />
            </div>
          </div>
        )}

        <CreateBranchModal
          open={createOpen}
          defaultPrompt={HERO_PROMPT}
          onSubmit={handleCreate}
          onClose={() => setCreateOpen(false)}
        />
        <ComparePanel />
        <KeyboardShortcutsOverlay open={shortcutsOpen} onClose={() => setShortcutsOpen(false)} />
        <ToastHost />
      </main>
    </div>
  );
}

function Stat({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-sm border border-line bg-surface px-3 py-1.5 font-mono text-[10.5px] font-medium uppercase tracking-eyebrow text-ink-muted shadow-panel">
      {children}
    </div>
  );
}
