# Milestone 2 — Worktree Lifecycle Backend

## What was built

### WorktreeService — `backend/app/services/worktree_service.py`

Full git subprocess implementation. All operations accept an optional `repo_path` override (used in tests).

| Method | Git command | What it does |
|---|---|---|
| `create_worktree(branch_name, worktree_path, parent_branch)` | `git worktree add -b` | Creates a branch and worktree directory |
| `delete_worktree(worktree_path, branch_name)` | `git worktree remove --force` + `git branch -D` | Removes worktree and branch |
| `get_diff(base_branch, branch_name)` | `git diff base...branch` | Returns unified diff string |
| `merge_branch(branch_name, target_branch)` | `git merge --no-ff` | Merges into target; raises `MergeConflictError` on conflict |

Custom exceptions:
- `WorktreeError` — base for all git operation failures
- `MergeConflictError` — subclass raised on merge conflicts (auto-aborts the failed merge)

Branch naming: `agent/{node_id}` — uses a dedicated namespace to avoid git ref conflicts with the parent branch name.

### New API endpoints — `backend/app/api.py`

| Method | Path | What it does |
|---|---|---|
| `POST` | `/api/v1/nodes/{id}/run` | Queues the node (stub — agent runner wired in Milestone 3) |
| `GET` | `/api/v1/nodes/{id}/diff` | Returns unified diff vs base branch |
| `POST` | `/api/v1/nodes/{id}/merge` | Merges branch into base; returns 409 on conflict |

Existing endpoints updated:
- `POST /nodes` now calls `create_worktree` on disk after creating the in-memory node
- `DELETE /nodes/{id}` now calls `delete_worktree` before removing the node from state

### New models — `backend/app/models.py`

- `DiffResponse` — `node_id`, `branch_name`, `base_branch`, `diff`, `has_changes`
- `MergeResponse` — `merged`, `node_id`, `branch_name`, `target_branch`, `message`
- `RunNodeResponse` — `node_id`, `status`, `message`
- New event types: `node.run_queued`, `node.merged`

### State fixes — `backend/app/state.py`

- `create_node` now generates the `GraphNode` (UUID-based ID) before planning the worktree, so `branch_name` and `worktree_path` correctly use the actual node ID
- Added `get_node(node_id)` — returns a single node copy
- Added `update_node_status(node_id, status)` — updates status and `updated_at`
- `delete_node` now returns the deleted node (needed by the API to get worktree path for cleanup)

---

## How to run

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Backend runs at `http://127.0.0.1:8000`.

---

## How to test

```bash
cd backend
uv run pytest -v
```

Expected: **18 passed**

```
tests/test_health.py::test_health
tests/test_repo_scaffold.py::test_repo_endpoint_exposes_demo_repo_config
tests/test_repo_scaffold.py::test_worktree_plan_endpoint_uses_parent_branch_shape
tests/test_repo_scaffold.py::test_branch_name_and_worktree_path_are_sanitized
tests/test_worktree_service.py::test_sanitize_strips_special_chars
tests/test_worktree_service.py::test_sanitize_collapses_dashes
tests/test_worktree_service.py::test_sanitize_empty_fallback
tests/test_worktree_service.py::test_build_branch_name_shape
tests/test_worktree_service.py::test_build_branch_name_sanitizes_inputs
tests/test_worktree_service.py::test_create_worktree_creates_directory_and_branch
tests/test_worktree_service.py::test_create_worktree_inherits_parent_content
tests/test_worktree_service.py::test_create_worktree_raises_on_invalid_repo
tests/test_worktree_service.py::test_delete_worktree_removes_directory_and_branch
tests/test_worktree_service.py::test_delete_worktree_is_idempotent
tests/test_worktree_service.py::test_get_diff_returns_empty_for_unmodified_branch
tests/test_worktree_service.py::test_get_diff_returns_changes_after_commit
tests/test_worktree_service.py::test_merge_branch_integrates_changes_into_target
tests/test_worktree_service.py::test_merge_branch_raises_on_conflict
```

---

## Manual smoke test

With the backend running and demo-repo set up:

```bash
# Create a node (also creates a real git worktree)
curl -s -X POST http://localhost:8000/api/v1/nodes \
  -H "Content-Type: application/json" \
  -d '{"label":"Rate limit approach A","parent_id":"root","prompt":"Add rate limiting to POST /api/login"}' | jq .

# Check diff (empty until agent makes changes)
curl -s http://localhost:8000/api/v1/nodes/<node_id>/diff | jq .

# Queue for run (stub until Milestone 3)
curl -s -X POST http://localhost:8000/api/v1/nodes/<node_id>/run | jq .

# Merge a branch
curl -s -X POST http://localhost:8000/api/v1/nodes/<node_id>/merge | jq .
```

Verify worktrees on disk:
```bash
cd demo-repo
git worktree list
```

---

## Verification checklist

- [x] Creating a node creates a real worktree on disk
- [x] Node metadata (branch_name, worktree_path) correctly reflects actual node ID
- [x] Deleting a node removes worktree and branch
- [x] Diff endpoint returns empty diff for unmodified branch
- [x] Diff endpoint returns unified diff after commits
- [x] Merge endpoint integrates branch into base branch
- [x] Merge conflict returns 409 and leaves repo clean
- [x] Run endpoint queues node and emits SSE event (stub)
- [x] 18/18 tests pass
