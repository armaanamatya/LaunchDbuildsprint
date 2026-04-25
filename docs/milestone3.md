# Milestone 3 — Agent Runner, SSE, Branch ×3, Reset, Status, Eval, Audit Log

> Backend layer that turns Milestone 2's worktree primitives into a live
> demo loop: spawn three differentiated agents from one prompt, watch them
> stream over SSE, get diffs and eval verdicts, merge a winner, reset for
> the next rehearsal — with a single readiness probe and a per-node audit
> trail for debugging.

---

## What was built

### Services

| File | Responsibility |
|---|---|
| `app/agent_runner/base.py` | `AgentRunner` ABC + `NormalizedEvent` + `StrategyHint` literal. |
| `app/agent_runner/mock_runner.py` | Deterministic offline runner. Three real, test-passing strategies (`route_local`, `dependency`, `middleware`). |
| `app/agent_runner/claude_runner.py` | Real `claude-agent-sdk` runner; per-strategy system-prompt biasing via `prompts.build_system_prompt`. |
| `app/agent_runner/prompts.py` | `CODING_SYSTEM_PROMPT` + `STRATEGY_HINTS` + `build_system_prompt(strategy)`. |
| `app/task_manager.py` | Background-task registry, `run_node_task` lifecycle, cancellation reasons, `_run_eval` + `node.eval_ready`. |
| `app/services/audit_log.py` | JSONL trace writer at `<worktree>/.agent-graph/trace.jsonl` (best-effort, never raises). |
| `app/state.py` | `GraphState.update_node_fields`, `reset_to_root`, `reset_for_tests`. |
| `app/events.py` | `EventBus.reset_for_tests`. |
| `app/services/worktree_service.py` | Strict-clean preflight (excluding linked worktrees), `DiffSummary`, `get_diff_summary` via `git diff --numstat`. |

### New endpoints (`app/api.py`)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/branches/triple` | Spawn 3 sibling agent branches (one per strategy); auto-runs by default. Preflight refuses when `enable_real_runs=true` without `ANTHROPIC_API_KEY` and `auto_run=true`. |
| `POST` | `/api/v1/demo/reset` | Cancel running tasks, remove every agent worktree + `agent/*` branch, hard-reset demo repo, re-seed via `scripts/reset_demo.py`, clear in-memory graph back to root. Emits `demo.reset` event. |
| `GET`  | `/api/v1/demo/status` | One-call readiness probe. `ready=true` only when demo-repo is clean, `enable_real_runs` either off or has a key, and there are zero active worktrees and zero running tasks. Never includes the API key value. |

### New event types (`app/models.py`)

- `node.eval_ready` (data: `passed`, `failed`, `summary`)
- `demo.reset` (data: `removed_worktrees`, `removed_branches`, `demo_repo_reset`)
- `agent.failed` carries `cancelled: true` + `error` reason when cancelled
- `node.diff_ready` payload extended with `files_changed`, `insertions`, `deletions` (computed via `git diff --numstat`)

### New models

`BranchTripleRequest`, `BranchTripleResponse`, `DemoResetResponse`,
`DemoStatusResponse`, `DiffSummary`, `NodeStrategy` literal,
`GraphNode.{strategy, eval_passed, eval_failed, eval_summary}`.

### Settings

| Key | Default | Purpose |
|---|---|---|
| `AGENT_GRAPH_ENABLE_EVAL` | `true` | Run `pytest tests/test_rate_limit.py` after `agent_completed`; emit `node.eval_ready`. |

(Existing keys unchanged.)

---

## How to run

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### Demo readiness

```bash
curl -s http://127.0.0.1:8000/api/v1/demo/status | jq
# Look for: { "ready": true, "issues": [] }
```

### Branch ×3 (the demo's central act)

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/branches/triple \
  -H "Content-Type: application/json" \
  -d '{"parent_id":"root","prompt":"Add rate limiting to POST /api/login"}' | jq
# Returns 3 nodes, one per strategy, each with status=running
```

Subscribe to live events:

```bash
curl -N http://127.0.0.1:8000/api/v1/graph/sse
# Watch agent.started → agent.text → agent.tool_use → agent.completed →
# node.diff_ready → node.eval_ready per node
```

### Diff + merge a winner

```bash
NODE=node-XXXXX
curl -s http://127.0.0.1:8000/api/v1/nodes/$NODE/diff | jq -r .diff
curl -s -X POST http://127.0.0.1:8000/api/v1/nodes/$NODE/merge | jq
```

### Reset between rehearsals

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/demo/reset | jq
# Returns counts of cleaned worktrees/branches; in-memory graph restored to root
```

---

## How to test

```bash
cd backend
uv run pytest -v
```

Expected: **66 passed** (plus the gated Claude smoke test which is skipped
unless `ANTHROPIC_API_KEY` AND `AGENT_GRAPH_RUN_REAL_SMOKE` are both set).

Real Claude smoke (optional):

```bash
ANTHROPIC_API_KEY=sk-... AGENT_GRAPH_RUN_REAL_SMOKE=1 \
  uv run pytest tests/test_claude_runner_smoke.py -v
```

---

## Verification checklist

- [x] Three differentiated mock strategies each write valid Python that takes
      `tests/test_rate_limit.py` to green (`tests/test_mock_strategies.py`).
- [x] `POST /branches/triple` returns 3 nodes (one per strategy), correctly
      handles `auto_run=true|false`, partial-failure resilience preserved
      (`tests/test_branch_triple.py`).
- [x] `POST /demo/reset` cleans worktrees + branches + working tree,
      idempotent, fails fast on missing demo repo (`tests/test_demo_reset.py`).
- [x] `GET /demo/status` reports `ready=true` only on a fresh, key-aligned,
      zero-worktree, zero-running-task backend; never leaks the API key
      value (`tests/test_demo_status.py`).
- [x] Worktree create refuses on dirty parent repo, allows linked worktrees
      to coexist, surfaces `/api/v1/demo/reset` on branch collisions
      (`tests/test_worktree_service.py`).
- [x] Cancellation reason propagates from caller → `agent.failed` event
      (`tests/test_task_manager_cancellation.py`).
- [x] Per-worktree JSONL trace at `<worktree>/.agent-graph/trace.jsonl`,
      best-effort writes never raise (`tests/test_audit_log.py`).
- [x] `node.diff_ready` payload includes `files_changed` / `insertions` /
      `deletions` from `git diff --numstat` (handles binaries cleanly)
      (`tests/test_diff_summary.py`).
- [x] Real Claude SDK runner double-gated by env vars
      (`tests/test_claude_runner_smoke.py`).
