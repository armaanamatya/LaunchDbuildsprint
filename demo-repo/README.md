# PulseDesk — Agent Graph demo target

A small FastAPI + SQLite "support inbox" app. This is the codebase the [Agent Graph](../README.md) agents operate on: each spawned branch is a `git worktree` of this repo, and the agents edit, run, and test code in here.

It is intentionally compact (one hero endpoint, one list endpoint, one mutate endpoint) so the diffs three sibling agents produce are short enough to read side by side in the compare view.

## What is included

- `POST /api/login` — hero endpoint for auth-like flows (the canonical "add rate limiting" target)
- `GET /api/tickets` — list/search endpoint
- `POST /api/tickets/{ticket_id}/reply` — mutate endpoint
- Seeded SQLite data with realistic tickets, agents, and message threads
- A reset script that recreates the database from a known baseline
- pytest coverage around the login endpoint plus baseline-reset behavior

## Run standalone

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8010
```

- App dashboard: <http://127.0.0.1:8010/>
- Inbox: <http://127.0.0.1:8010/inbox>
- Docs: <http://127.0.0.1:8010/docs>

(You don't need to run this for Agent Graph to work — the backend operates on the repo via `git worktree` directly.)

## Reset

```bash
uv run python scripts/reset_demo.py
```

Deletes the current SQLite file and rebuilds the seeded baseline.

## Test

```bash
uv run pytest
```

## Demo credentials

- `alex@pulsedesk.test` / `demo123`
- `priya@pulsedesk.test` / `demo123`
- `sam@pulsedesk.test` / `demo123` (seeded inactive — for negative-path tests)

## Agent Graph integration

The backend defaults to `../demo-repo` relative to itself, so no configuration is needed if you cloned the full project. To point it elsewhere:

```bash
export AGENT_GRAPH_DEMO_REPO_PATH=/absolute/path/to/demo-repo
```
