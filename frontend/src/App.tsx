import { startTransition, useEffect, useMemo, useState } from "react";
import { ComparePanel } from "./components/ComparePanel";
import { ConnectionIndicator } from "./components/ConnectionIndicator";
import { CreateBranchModal } from "./components/CreateBranchModal";
import { DetailPanel } from "./components/DetailPanel";
import { EmptyStateCTA } from "./components/EmptyStateCTA";
import { GraphView } from "./components/GraphView";
import { KeyboardShortcutsOverlay } from "./components/KeyboardShortcutsOverlay";
import { StatusPaletteSwatch } from "./components/StatusPaletteSwatch";
import { StatusStrip } from "./components/StatusStrip";
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

const DRAWER_WIDTH = "26rem";

// Z-index discipline:
//   z-10 — content (hero, graph)
//   z-20 — chrome (toolbar, connection, drawer, status strip)
//   z-30 — overlays (modals, ComparePanel sheet, toasts, shortcuts overlay)

export function App() {
  if (typeof window !== "undefined" && new URLSearchParams(window.location.search).get("palette") === "1") {
    return <StatusPaletteSwatch />;
  }
  const graph = useGraphStore((s) => s.graph);
  const selectedNodeId = useGraphStore((s) => s.selectedNodeId);
  const loadGraph = useGraphStore((s) => s.loadGraph);
  const selectNode = useGraphStore((s) => s.selectNode);
  const createBranch = useGraphStore((s) => s.createBranch);
  const spawnTriple = useGraphStore((s) => s.spawnTriple);
  const runBranch = useGraphStore((s) => s.runBranch);
  const mergeBranch = useGraphStore((s) => s.mergeBranch);
  const openCompare = useGraphStore((s) => s.openCompare);
  const resetDemo = useGraphStore((s) => s.resetDemo);

  const [createOpen, setCreateOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);

  const handleCreate = async (label: string, prompt: string) => {
    await createBranch(label, prompt);
  };

  const handleQuickStart = async (prompt: string = HERO_PROMPT) => {
    await spawnTriple(prompt);
  };

  useGraphSSE();

  const branchCount = graph.nodes.filter((n) => n.parent_id !== null).length;
  const isEmpty = branchCount === 0;
  const selectedNode = useMemo(
    () => graph.nodes.find((node) => node.id === selectedNodeId) ?? graph.nodes[0],
    [graph.nodes, selectedNodeId],
  );
  const showDetailPanel = Boolean(
    !isEmpty && selectedNode && selectedNode.parent_id !== null,
  );
  const completedNodeCount = graph.nodes.filter(
    (node) => node.status === "completed" || node.status === "merged",
  ).length;

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

  // Reserve space on the right for the drawer when it's open. CSS transitions
  // smooth the layout shift; ReactFlow re-fits inside GraphView once the
  // container width settles.
  const reservedRight = showDetailPanel ? DRAWER_WIDTH : "0rem";

  return (
    <div className="min-h-screen bg-paper text-ink">
      <main className="relative min-h-screen overflow-hidden">
        {/* Canvas area — shrinks via paddingRight when drawer opens */}
        <div
          className="relative h-screen transition-[padding] duration-300 ease-out"
          style={{ paddingRight: reservedRight }}
        >
          {isEmpty ? (
            <div className="absolute inset-0 blueprint-bg">
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_30%,rgba(216,73,46,0.05),transparent_55%)]" />
              {/* Decorative ghost branches — telegraphs what spawning produces */}
              <svg
                aria-hidden
                className="absolute left-1/2 top-[68%] h-[260px] w-[640px] -translate-x-1/2"
                viewBox="0 0 640 260"
                fill="none"
                stroke="currentColor"
                strokeWidth="1"
                strokeDasharray="4 6"
                style={{ color: "rgba(26, 26, 29, 0.08)" }}
              >
                <path d="M320 0 C 200 80, 140 160, 120 240" />
                <path d="M320 0 L 320 240" />
                <path d="M320 0 C 440 80, 500 160, 520 240" />
              </svg>
            </div>
          ) : (
            <GraphView
              graph={graph}
              selectedNodeId={selectedNodeId}
              onSelectNode={selectNode}
            />
          )}

          {isEmpty && (
            <EmptyStateCTA
              defaultPrompt={HERO_PROMPT}
              onSubmit={handleQuickStart}
              onCreate={() => setCreateOpen(true)}
            />
          )}
        </div>

        {/* Toolbar — top-left, sits in the (shrunken) main area */}
        <div
          className="pointer-events-none absolute top-0 left-0 z-20 p-4 sm:p-6 transition-[padding] duration-300 ease-out"
          style={{ right: reservedRight }}
        >
          <div className="flex items-start gap-3">
            <div className="pointer-events-auto min-w-0">
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
          </div>
        </div>

        {/* Connection indicator — fixed top-right, slides with drawer */}
        <div
          className="pointer-events-none absolute top-0 z-20 hidden p-4 sm:p-6 md:block transition-[right] duration-300 ease-out"
          style={{ right: reservedRight }}
        >
          <ConnectionIndicator />
        </div>

        {/* Status strip — fixed bottom-left, only when populated */}
        {!isEmpty && (
          <div
            className="pointer-events-none absolute bottom-0 left-0 z-20 p-4 sm:p-6 transition-[padding] duration-300 ease-out"
            style={{ right: reservedRight }}
          >
            <div className="pointer-events-auto inline-block">
              <StatusStrip branchCount={branchCount} />
            </div>
          </div>
        )}

        {/* Drawer — fixed to viewport right edge */}
        {showDetailPanel && selectedNode && (
          <div
            className="pointer-events-none fixed right-0 top-0 z-20 flex h-full items-stretch p-4 pt-24 sm:p-6 sm:pt-24"
            style={{ width: DRAWER_WIDTH }}
          >
            <DetailPanel node={selectedNode} onClose={() => selectNode("root")} />
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
