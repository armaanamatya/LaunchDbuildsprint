# Future Agent Prompt: Node Decision Summaries

You are implementing an additive feature in Agent Graph. Treat this as a
product-critical UX improvement, not a redesign.

## Goal

Add a modular per-node "Decision Summary" feature that helps users understand
and choose between multiple agent-created branches without opening several IDEs,
terminals, branches, or worktrees.

The feature must preserve the existing graph, node cards, selected-branch panel,
diff flow, logs, eval events, and merge flow. Do not overwrite or redesign the
current UI. Add small, composable surfaces that can survive a future UI refactor.

The product promise:

> Each graph node represents a real implementation branch. The summary explains
> what the agent did, whether it worked, how risky it is, and whether it is a
> good merge candidate.

## Current Relevant Files

Backend:

- `backend/app/models.py`
- `backend/app/state.py`
- `backend/app/task_manager.py`
- `backend/app/services/worktree_service.py`
- `backend/app/services/audit_log.py`
- `backend/tests/`

Frontend:

- `frontend/src/types.ts`
- `frontend/src/App.tsx`
- `frontend/src/components/WorktreeNode.tsx`
- `frontend/src/components/StatusBadge.tsx`
- `frontend/src/store/graphStore.ts`

Existing data:

- `GraphNode.summary` is a simple string. Keep it for backwards compatibility.
- `GraphNode.eval_passed`, `eval_failed`, and `eval_summary` already exist.
- `node.diff_ready` and `node.eval_ready` already exist.

## Recommended Scope

Implement deterministic summaries first. Do not call an LLM to summarize. The
first version should be fast, stable, cheap, and demo-safe.

### Backend Additions

1. Add structured models in `backend/app/models.py`:

```python
SummaryRisk = Literal["low", "medium", "high", "unknown"]
SummaryRecommendation = Literal["merge_candidate", "needs_review", "do_not_merge"]

class NodeDecisionSummary(BaseModel):
    version: int = 1
    headline: str
    approach: str
    changed_files: list[str] = Field(default_factory=list)
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    tests_passed: int | None = None
    tests_failed: int | None = None
    test_summary: str | None = None
    risk: SummaryRisk = "unknown"
    risk_reason: str
    recommendation: SummaryRecommendation = "needs_review"
    review_focus: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=utc_now)
```

2. Extend `GraphNode` additively:

```python
decision_summary: NodeDecisionSummary | None = None
```

Do not remove or repurpose `summary`.

3. Add event type:

```python
"node.summary_ready"
```

4. Add a service:

```text
backend/app/services/node_summary.py
```

Suggested API:

```python
def build_decision_summary(
    *,
    node: GraphNode,
    diff_text: str,
    changed_files: list[str],
    files_changed: int,
    insertions: int,
    deletions: int,
    tests_passed: int | None,
    tests_failed: int | None,
    test_summary: str | None,
) -> NodeDecisionSummary:
    ...

def write_summary(worktree_path: str, summary: NodeDecisionSummary) -> None:
    ...
```

Write JSON to:

```text
<worktree>/.agent-graph/summary.json
```

Like `audit_log.write`, this must be best-effort and must never crash an agent
run.

5. Add or extend worktree diff helpers if needed:

- Use git, not ad hoc diff parsing, for changed file names.
- Prefer `git diff --name-only <base>...<branch>`.
- Keep binary files safe.
- Cap long file lists in the UI, but preserve full list in JSON.

6. Hook summary generation in `backend/app/task_manager.py`.

Current flow after `agent_completed`:

- update node status to `completed`
- compute diff
- emit `node.diff_ready`
- run eval
- emit `node.eval_ready`

Desired flow:

- compute diff summary
- run eval if enabled
- build decision summary using diff + eval data
- update `graph_state.update_node_fields(node_id, summary=..., decision_summary=...)`
- emit `node.summary_ready`
- write `.agent-graph/summary.json`

Important: If eval is disabled, missing, times out, or cannot run, still produce
a summary with `risk="unknown"` or `risk="medium"` and
`recommendation="needs_review"`.

7. Keep compatibility with existing SSE clients.

Existing events must continue to work. `node.summary_ready` is additive. It
should include the structured summary in `data.summary`, but frontend should
also work from periodic `/graph` snapshots.

### Deterministic Summary Heuristics

Use simple transparent rules.

Approach:

- `route_local` -> `Route-local guard`
- `dependency` -> `FastAPI dependency`
- `middleware` -> `ASGI middleware`
- otherwise -> `Custom branch`

Headline examples:

- `"Adds rate limiting with a FastAPI dependency"`
- `"Adds rate limiting with ASGI middleware"`
- `"No code changes detected"`
- `"Run failed before producing a mergeable change"`

Risk:

- `high` if `tests_failed > 0`
- `high` if no changed files on a completed node
- `medium` if eval did not run or test counts are unknown
- `medium` if `files_changed > 5`
- `medium` if `insertions + deletions > 300`
- `low` if tests pass, changed files exist, and diff is small/medium

Recommendation:

- `merge_candidate` if tests passed, zero failed, and changes exist
- `do_not_merge` if tests failed or no changes were produced
- `needs_review` otherwise

Review focus:

- Include up to 4 concise bullets.
- Mention changed critical files.
- Mention missing eval.
- Mention large diff size.
- Mention failed tests.

Do not infer beyond available data. It is acceptable for the first version to be
plain and deterministic.

### Frontend Additions

1. Extend `frontend/src/types.ts`.

Add:

```ts
export type SummaryRisk = "low" | "medium" | "high" | "unknown";
export type SummaryRecommendation =
  | "merge_candidate"
  | "needs_review"
  | "do_not_merge";

export interface NodeDecisionSummary {
  version: number;
  headline: string;
  approach: string;
  changed_files: string[];
  files_changed: number;
  insertions: number;
  deletions: number;
  tests_passed: number | null;
  tests_failed: number | null;
  test_summary: string | null;
  risk: SummaryRisk;
  risk_reason: string;
  recommendation: SummaryRecommendation;
  review_focus: string[];
  generated_at: string;
}
```

Extend `GraphNode`:

```ts
decision_summary: NodeDecisionSummary | null;
```

Make local mock/initial nodes include `decision_summary: null` so type checks
stay clean.

2. Add component:

```text
frontend/src/components/NodeSummaryCard.tsx
```

Props:

```ts
type NodeSummaryCardProps = {
  node: GraphNode;
  compact?: boolean;
};
```

Behavior:

- If `node.decision_summary` exists, render structured summary.
- If not, render a small pending/empty state based on node status:
  - running: "Summary will appear after the agent finishes."
  - idle/queued: "Run this branch to generate a decision summary."
  - failed: "No summary generated. Check logs and diff."
- Do not fetch data inside this component.
- Do not mutate state inside this component.
- Keep styling local and consistent with existing dark panel/cards.

3. Integrate into `frontend/src/App.tsx` selected branch panel.

Place `NodeSummaryCard` below the selected branch title/status and above
worktree path metadata.

Do not remove the existing prompt, path, timestamp, or status details. This is
an additive card.

4. Add component:

```text
frontend/src/components/BranchSummaryCompare.tsx
```

Props:

```ts
type BranchSummaryCompareProps = {
  nodes: GraphNode[];
  onSelectNode: (nodeId: string) => void;
};
```

Render only completed/merged/failed nodes that have either `decision_summary`,
`eval_summary`, or `summary`.

Initial placement:

- In `App.tsx`, add a compact bottom-left or top-right compare strip only when
  at least 2 completed/merged nodes exist.
- Keep it visually secondary to the graph.
- Do not turn it into a modal or replace the graph.

If layout risk is high, skip this component in the first implementation and
only ship `NodeSummaryCard`.

5. Optional tiny node badges in `WorktreeNode.tsx`.

Add only if it stays uncluttered:

- test count badge
- risk badge
- recommendation icon/text

Do not resize the node card dynamically in a way that breaks graph layout. If
text may overflow, hide overflow or use short fixed labels.

## UX Ranking

Build in this order:

1. `NodeSummaryCard` in selected branch panel.
2. Backend deterministic summary + `node.summary_ready`.
3. Compare strip/cards for completed nodes.
4. Tiny graph-node badges.
5. Merge-confirmation summary.

The first two are the real MVP. They directly solve the user pain: "I cannot
understand multiple branches quickly."

## Edge Cases

Handle all of these gracefully:

- Agent fails before making changes.
- Agent completes but commits nothing.
- Eval disabled.
- `uv` missing.
- Eval timeout.
- Tests fail.
- Diff cannot be computed.
- Worktree deleted before summary write.
- Branch deleted before summary generation.
- Binary files in diff.
- Very large diff.
- Huge file list.
- Backend restarts after branches still exist.
- Frontend sees old nodes without `decision_summary`.
- Multiple agents complete close together.

Rules:

- Summary generation must never make a successful run fail.
- Missing data should produce an honest `needs_review` summary.
- Do not block merge on summary generation.
- Do not hide raw diff/logs behind the summary.
- Summary is advisory, not authoritative.

## Scale Considerations

Do not build a database in this feature.

Design for future persistence by keeping `NodeDecisionSummary` JSON-serializable
and versioned. Storing it in both in-memory node state and
`<worktree>/.agent-graph/summary.json` is enough for the hackathon.

Avoid storing full diffs in the summary object. Store counts, file names, and
short text only.

Avoid frontend components that assume exactly three branches. The demo uses
three, but the component should work with any number of nodes.

## Test Plan

Backend tests:

- `test_node_summary.py`
  - passed eval + small diff -> low risk, merge candidate
  - failed eval -> high risk, do not merge
  - no eval -> needs review
  - no changed files -> high risk, do not merge
  - large diff -> medium risk
  - writes valid `.agent-graph/summary.json`

- Extend `test_diff_summary.py` or `test_worktree_service.py`
  - changed file list helper handles normal and binary-safe diffs

- Extend task-manager tests
  - after `agent_completed`, emits `node.summary_ready`
  - node has `decision_summary`
  - summary generation failure logs/warns but does not fail run

Frontend tests if test framework is present:

- `NodeSummaryCard` renders structured summary.
- `NodeSummaryCard` renders pending state.
- `BranchSummaryCompare` renders multiple completed nodes and calls
  `onSelectNode`.

Manual verification:

```bash
cd backend
uv run pytest -q

cd ../frontend
npm run build
```

If frontend build tooling is not already installed, report that instead of
adding unrelated setup.

## Non-Goals

- Do not replace existing selected-branch panel.
- Do not create a new app layout.
- Do not remove raw logs, diffs, eval details, or merge controls.
- Do not add LLM summarization yet.
- Do not add database persistence.
- Do not push to GitHub automatically.
- Do not make merge automatic based on recommendation.

## Done Definition

The feature is done when:

- A completed node gets a structured decision summary.
- The summary is visible in the selected-branch panel.
- Existing graph, diff, eval, and merge behavior still works.
- Missing/failed eval still yields an honest summary.
- Backend tests pass.
- Frontend builds.

The demo line should become:

> Agent Graph does not just run three agents. It summarizes each branch into a
> decision card so you can compare work, understand risk, and merge the right
> implementation without juggling IDE windows.
