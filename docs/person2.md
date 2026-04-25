# Person 2 Final Handoff

Updated: 2026-04-25 16:53:28 CDT (-0500)

Audience: users, demo operators, and future agents working on the Person 2
backend/git/agent-runtime slice.

## Scope

Person 2 owns the FastAPI backend, git worktree lifecycle, agent runner
runtime, SSE events, diff/merge flow, demo reset/readiness, backend tests, and
backend-facing documentation.

Out of scope by plan: `frontend/**`, `prompt.txt`, Person 1 demo content, and
production/GitHub-app/analytics work. `frontend/src/types.ts` was still touched
as backend contract sync, so treat that as a coordination item with Person 3.

## What Was Built

| Area | Result | Main files |
|---|---|---|
| Strategy plumbing | `NodeStrategy` (`route_local`, `dependency`, `middleware`) flows through node creation, graph state, runners, and frontend contract types. | `backend/app/models.py`, `backend/app/state.py`, `backend/app/agent_runner/base.py`, `frontend/src/types.ts` |
| Mock runner strategies | Offline mock runner now writes three distinct, real, test-passing rate-limit implementations. | `backend/app/agent_runner/mock_runner.py` |
| Claude strategy prompts | Claude runner receives strategy-specific system prompt bias. | `backend/app/agent_runner/claude_runner.py`, `backend/app/agent_runner/prompts.py` |
| Branch x3 endpoint | `POST /api/v1/branches/triple` creates three sibling nodes, one per strategy, and can auto-run them. | `backend/app/api.py` |
| Run preflight | Real-run endpoints refuse auto-run without `ANTHROPIC_API_KEY` when `AGENT_GRAPH_ENABLE_REAL_RUNS=true`. | `backend/app/api.py`, `backend/app/settings.py` |
| Demo reset | `POST /api/v1/demo/reset` cancels runs, removes worktrees, sweeps all durable `agent/*` branches, resets base branch to stored baseline ref, cleans untracked dirt, reseeds demo DB, clears graph state. | `backend/app/api.py`, `backend/app/state.py`, `backend/app/task_manager.py` |
| Demo status | `GET /api/v1/demo/status` reports one-call readiness: repo presence, git state, dirtiness, worktrees, API key presence, eval/uv readiness, running tasks, issues. | `backend/app/api.py`, `backend/app/models.py` |
| Eval | After `agent.completed`, backend can run `uv run pytest tests/test_rate_limit.py` and emit `node.eval_ready`. | `backend/app/task_manager.py`, `backend/app/settings.py` |
| Cancellation reasons | Cancels publish `agent.failed` with a caller-specific reason and `cancelled: true`. | `backend/app/task_manager.py`, `backend/app/api.py` |
| Audit log | Agent events are written to `<worktree>/.agent-graph/trace.jsonl`, best effort. | `backend/app/services/audit_log.py`, `backend/app/task_manager.py` |
| Diff summary | `node.diff_ready` includes `files_changed`, `insertions`, `deletions`, backed by git numstat logic. | `backend/app/services/worktree_service.py`, `backend/app/task_manager.py` |
| Worktree hardening | `create_worktree` blocks dirty parent repos, ignores linked worktree dirs, and gives reset guidance on collisions. | `backend/app/services/worktree_service.py` |
| Test isolation | Shared fixture resets cached settings, graph state, task manager, and event bus around temp git repos. | `backend/tests/conftest.py` |

## API Contract

| Method | Path | Contract |
|---|---|---|
| `POST` | `/api/v1/branches/triple` | Body: `parent_id`, `prompt`, optional `label_prefix`, optional `auto_run`. Returns three attempted nodes, including failed nodes if one strategy fails worktree creation. |
| `POST` | `/api/v1/nodes/{id}/run` | Starts one node run unless root/running/invalid state. Requires key only when real runs are enabled. |
| `GET` | `/api/v1/nodes/{id}/diff` | Returns full diff plus `has_changes`. |
| `POST` | `/api/v1/nodes/{id}/merge` | Merges selected agent branch into configured base branch. |
| `POST` | `/api/v1/demo/reset` | Canonical rehearsal reset path. Restores the configured base branch to the stored demo baseline ref and removes both tracked and untracked rehearsal dirt. |
| `GET` | `/api/v1/demo/status` | Readiness probe. Never returns the API key value. |
| `GET` | `/api/v1/graph/sse` | Global SSE stream for graph and agent events. |
| `GET` | `/api/v1/nodes/{id}/sse` | Node-filtered SSE stream plus heartbeats. |

## Events And Models

New or expanded models:

- `NodeStrategy`
- `BranchTripleRequest`
- `BranchTripleResponse`
- `DemoResetResponse`
- `DemoStatusResponse`
- `DiffSummary`
- `GraphNode.strategy`
- `GraphNode.eval_passed`
- `GraphNode.eval_failed`
- `GraphNode.eval_summary`

New or expanded event types:

- `node.eval_ready`
- `demo.reset`
- `agent.failed` with cancellation metadata
- `node.diff_ready` with diff summary totals

## Settings

| Setting | Default | Meaning |
|---|---|---|
| `AGENT_GRAPH_ENABLE_REAL_RUNS` | `false` | Use Claude runner instead of mock runner when true. |
| `ANTHROPIC_API_KEY` | unset | Required only for real auto-runs. Value is never exposed by status. |
| `AGENT_GRAPH_ENABLE_EVAL` | `true` | Run rate-limit pytest eval after completion. |
| `AGENT_GRAPH_DEMO_REPO_PATH` | auto-detect `demo-repo` | Demo repo root. |
| `AGENT_GRAPH_BASE_BRANCH` | `main` | Base branch for worktrees, diffs, merges, reset. |
| `AGENT_GRAPH_DEMO_BASELINE_REF` | `refs/agent-graph/demo-baseline` | Internal ref used by reset to restore the hero-task baseline after a merge. |
| `AGENT_GRAPH_WORKTREE_DIR` | `.agent-worktrees` | Worktree directory under demo repo. |

Baseline note: the ref is initialized before backend-managed branch creation or
merge. If an existing repo was already polluted before the ref existed,
recreate the demo repo or repoint `AGENT_GRAPH_DEMO_BASELINE_REF` to the clean
hero-task commit.

## Tests Added Or Expanded

| Task | Test file | Coverage |
|---|---|---|
| P2-A | `backend/tests/test_mock_strategies.py` | Three mock strategies patch real demo repo copies, parse, stay idempotent, and pass rate-limit tests. |
| P2-B | `backend/tests/test_branch_triple.py` | Branch x3 happy path, auto-run events, 404, key preflight, partial worktree failure. |
| P2-C | `backend/tests/test_demo_reset.py` | Reset removes in-memory nodes, configured worktree root, stale durable/current agent branches, untracked dirt, and restores the stored baseline after `main` moves. |
| P2-D | `backend/tests/test_demo_status.py` | Ready state, dirty repo, leaked worktrees, missing key, missing `uv` when eval is enabled, key masking. |
| P2-E | `backend/tests/test_worktree_service.py` | Dirty repo guard, linked-worktree exclusion, branch collision guidance, diff summary. |
| P2-F | `backend/tests/test_task_manager_cancellation.py` | Cancellation reason reaches `agent.failed`. |
| P2-G | `backend/tests/test_audit_log.py` | JSONL trace file exists, parses, and records terminal event. |
| P2-H | `backend/tests/test_claude_runner_smoke.py` | Real Claude smoke, double gated by `ANTHROPIC_API_KEY` and `AGENT_GRAPH_RUN_REAL_SMOKE`. |
| P2-I | `backend/tests/test_diff_summary.py` | Diff stats from fixtures, including non-text/binary-safe cases. |
| P2-J | `docs/milestone3.md`, `docs/demo-worktree-hygiene.md`, `docs/plan-personB.md` | Backend/demo contract documentation. |

## Verification Snapshot

Commands run during review:

```bash
cd backend
uv run pytest tests/test_branch_triple.py tests/test_task_manager_cancellation.py -q
# 7 passed

uv run pytest tests/test_mock_strategies.py tests/test_demo_reset.py tests/test_demo_status.py tests/test_worktree_service.py -q
# 39 passed
```

Expected full backend command:

```bash
cd backend
uv run pytest -v
```

`tests/test_claude_runner_smoke.py` is expected to skip unless both
`ANTHROPIC_API_KEY` and `AGENT_GRAPH_RUN_REAL_SMOKE` are set.

## Review Items Resolved

The latest reset/readiness review items are covered by code and tests:

1. Reset targets the stored baseline ref (`refs/agent-graph/demo-baseline` by
   default), not current `main`.

2. Reset runs `git clean -fd` after `git reset --hard <baseline>`, so
   untracked non-ignored dirt is removed.

3. `/api/v1/demo/status` returns `ready=false` when eval is enabled and `uv`
   is not on `PATH`.

4. Reset sweeps durable `agent/*` branches from git even if `graph_state` was
   lost after a backend restart.

## Workspace Hygiene Notes

Generated or local-only paths currently appear in the working tree and should
not be included in a clean Person 2 commit unless intentionally justified:

- `backend/venv/`
- `backend/build/`
- `backend/agent_graph_backend.egg-info/`
- `demo-repo/.agent-worktrees/`
- `.codex`

Files that are part of the Person 2 implementation and should be included if
the feature is committed:

- `backend/app/**`
- `backend/tests/test_*`
- `backend/tests/conftest.py`
- `backend/pyproject.toml`
- `backend/uv.lock`
- `docs/person2.md`
- `docs/milestone3.md`
- `docs/demo-worktree-hygiene.md`
- `docs/active-change-critique.md`

Coordinate `frontend/src/types.ts` with Person 3 before committing because it
is outside the original Person 2 scope but reflects backend API shape.
