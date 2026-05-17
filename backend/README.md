# Agent Graph Backend

FastAPI service that owns the graph state, the SSE event bus, git-worktree CRUD, and the agent task manager. See [the root README](../README.md) for the project overview and [`docs/architecture.md`](../docs/architecture.md) for how this piece fits in.

## Run

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

OpenAPI docs at <http://127.0.0.1:8000/docs>.

## Configuration

All settings are environment variables (also read from a local `.env`). Defaults work out of the box for the bundled `demo-repo/`.

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required only when `AGENT_GRAPH_ENABLE_REAL_RUNS=true` |
| `AGENT_GRAPH_ENABLE_REAL_RUNS` | `false` | Set `true` to use real Claude agents instead of mocks |
| `AGENT_GRAPH_ENABLE_EVAL` | `true` | Run `uv run pytest` per branch after agent completes |
| `AGENT_GRAPH_DEMO_REPO_PATH` | `../demo-repo` | Absolute or relative path to the target repo |
| `AGENT_GRAPH_BASE_BRANCH` | `main` | The branch agent branches derive from |
| `AGENT_GRAPH_WORKTREE_DIR` | `.agent-worktrees` | Subdirectory of the demo repo for worktrees |
| `AGENT_GRAPH_MAX_RUN_SECONDS` | `600` | Wall-clock cap per agent run |
| `AGENT_GRAPH_HOST` / `_PORT` | `127.0.0.1` / `8000` | Bind address |
| `AGENT_GRAPH_CORS_ORIGINS` | localhost:5173 | Comma-separated list |

## Layout

```
app/
├── main.py              FastAPI app + CORS
├── api.py               All HTTP/SSE routes (single router)
├── events.py            EventBus — async fan-out with per-subscriber predicates
├── state.py             In-memory graph state (nodes/edges)
├── task_manager.py      Tracks running agent tasks, cancellation, lifecycle
├── settings.py          pydantic-settings config
├── models.py            Pydantic request/response/event types
├── agent_runner/        claude-agent-sdk wrapper + mock implementations
└── services/            repo_service, worktree_service
tests/                   pytest suite covering API, worktree, eval
```

## Test

```bash
uv run pytest
```

## API reference

See [`../docs/api.md`](../docs/api.md) for the REST endpoints and SSE event schema.
