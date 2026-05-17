# API Reference

All routes are prefixed `/api/v1`. The full live OpenAPI is at <http://127.0.0.1:8000/docs> when the backend is running.

## REST

### Graph

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness probe. Returns `{status: "ok", app}`. |
| `GET` | `/graph` | Full graph snapshot — nodes, edges, base branch, worktree root. |
| `GET` | `/repo` | Repo config — resolved demo-repo path, base branch, whether `.git` exists. |
| `GET` | `/demo/status` | One-call readiness probe. `ready: true` only when every prereq passes and no agents are running. Use this to gate the UI's "Spawn 3" button. |
| `POST` | `/demo/reset` | Cancel running agents, delete every agent worktree + branch, hard-reset demo-repo to its baseline ref, re-seed the SQLite database. |

### Nodes

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/nodes` | Create a single child node from a parent. Body: `{label, parent_id, prompt?, strategy?}`. |
| `POST` | `/branches/triple` | Create three sibling nodes from one parent — one per strategy — and (by default) start them immediately. Body: `{parent_id, prompt, label_prefix?, auto_run?}`. This is the canonical "Branch ×3" endpoint. |
| `DELETE` | `/nodes/{id}` | Delete a node, cancel its task, remove its worktree. Cannot delete `root`. |
| `POST` | `/nodes/{id}/run` | Start (or restart) the agent run for an existing node. Streams progress over SSE; returns immediately. |
| `GET` | `/nodes/{id}/diff` | `git diff` between the base branch and this node's branch. Returns the raw diff text plus `has_changes`. |
| `POST` | `/nodes/{id}/merge` | Merge this node's branch into `base_branch`. Returns 409 on conflict. |
| `GET` | `/nodes/{id}/worktree-plan` | Utility: what worktree path/branch name *would* be assigned for this node. |

### Strategies

`strategy` is one of `route_local`, `dependency`, `middleware`. Each biases both the mock implementation and the Claude system prompt so the three siblings diverge meaningfully. See `backend/app/agent_runner/`.

### Node status

`idle` → `queued` → `running` → (`completed` | `failed`) → optionally `merged`.

Status values are defined in `backend/app/models.py:NodeStatus`. The frontend renders `queued` with a "creating" palette — see [`frontend/docs/tokens.md`](../frontend/docs/tokens.md#status-palette-six-values-six-hues).

---

## SSE

Two streams. Both follow standard `text/event-stream` framing: `event: <type>\ndata: <json>\n\n`.

### `GET /api/v1/graph/sse`

Global stream — receives every event for every node.

First message after connect is always `graph.connected` with `{base_branch, worktree_root}`. After 10 seconds of silence the server emits a `heartbeat` event so clients/proxies don't time out.

### `GET /api/v1/nodes/{id}/sse`

Per-node stream — filtered at the event bus (not by JSON scraping) so only events with `node_id == {id}` are delivered. Heartbeats still pass through.

### Event types

Defined in `backend/app/models.py:GraphEventType`. Every event has `{type, timestamp, node_id?, data}`.

**Graph lifecycle**

| Type | When | `data` shape |
|---|---|---|
| `graph.connected` | First event on `/graph/sse` | `{base_branch, worktree_root}` |
| `node.created` | After `POST /nodes` or `POST /branches/triple` | `{node}` (full `GraphNode`); on creation failure includes `error` |
| `node.updated` | Status transitions, eval results | `{node}` |
| `node.deleted` | After `DELETE /nodes/{id}` | `{node_id}` |
| `node.run_queued` | Run accepted by task manager | `{}` |
| `node.merged` | After successful merge | `{branch_name, target_branch}` |
| `node.diff_ready` | Diff computed (post-completion) | `{node_id}` |
| `node.eval_ready` | Test run finished | `{passed, failed, summary}` |
| `demo.reset` | After `POST /demo/reset` | `{removed_worktrees, removed_branches, demo_repo_reset}` |

**Agent lifecycle**

| Type | When | `data` shape |
|---|---|---|
| `agent.started` | Runner begins | `{strategy, prompt}` |
| `agent.text` | Streamed assistant text | `{text}` |
| `agent.tool_use` | Claude invokes a tool | `{name, input}` |
| `agent.tool_result` | Tool result returned | `{name, result}` |
| `agent.completed` | Run finished successfully | `{summary?, files_changed?}` |
| `agent.failed` | Run errored or timed out | `{error}` |

**Connection**

| Type | When |
|---|---|
| `heartbeat` | Every 10s of idle on each stream |

---

## Authoritative sources

If this document and the code disagree, the code wins. Models are defined once in `backend/app/models.py`; the TypeScript mirror lives in `frontend/src/types.ts`.
