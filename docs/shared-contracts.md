# Agent Graph Shared Contracts

These are the Milestone 0 contracts that both the frontend and backend use.

## Graph Node

- `id`: stable node identifier
- `label`: human-friendly name shown in the graph
- `status`: one of `idle`, `queued`, `running`, `completed`, `failed`, `merged`
- `branch_name`: git branch represented by the node
- `worktree_path`: local worktree path for the node
- `parent_id`: parent node id, or `null` for the root node
- `prompt`: task prompt attached to the node
- `summary`: short branch summary for the side panel
- `created_at`: ISO timestamp
- `updated_at`: ISO timestamp

## Graph Snapshot

- `nodes`: list of graph nodes
- `edges`: source-target connections derived from `parent_id`
- `base_branch`: root branch for the prepared repo
- `worktree_root`: directory that will hold branch worktrees

## Graph Events

- `graph.connected`
- `node.created`
- `node.updated`
- `node.deleted`
- `heartbeat`

The Python definitions live in `backend/app/models.py`, and the matching TypeScript definitions live in `frontend/src/types.ts`.
