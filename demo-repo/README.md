# PulseDesk Demo Repo

Small FastAPI + SQLite support inbox app prepared for Agent Graph demos.

## What is included

- `POST /api/login` hero endpoint for auth-like flows
- `GET /api/tickets` list/search endpoint
- `POST /api/tickets/{ticket_id}/reply` mutate endpoint
- seeded SQLite data with realistic tickets, agents, and message threads
- a reset script that recreates the database from a known baseline
- pytest coverage around the login endpoint plus baseline reset behavior

## Run

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8010
```

Open:

- app dashboard: `http://127.0.0.1:8010/`
- inbox: `http://127.0.0.1:8010/inbox`
- docs: `http://127.0.0.1:8010/docs`

## Reset

```bash
uv run python scripts/reset_demo.py
```

That command deletes the current SQLite file and rebuilds the seeded baseline.

## Test

```bash
uv run pytest
```

## Demo Credentials

- `alex@pulsedesk.test` / `demo123`
- `priya@pulsedesk.test` / `demo123`

There is also an inactive seeded account for negative-path tests:

- `sam@pulsedesk.test` / `demo123`

## Agent Graph Integration

Point Agent Graph at this prepared repo with:

```bash
AGENT_GRAPH_DEMO_REPO_PATH=C:\Users\Armaan\Desktop\beatmyyeet\demo-repo
```

The backend already reads that path from `AGENT_GRAPH_DEMO_REPO_PATH`.

