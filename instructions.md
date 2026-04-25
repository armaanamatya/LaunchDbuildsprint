# Real Demo Instructions

## 1. Prepare Demo Repo

`demo-repo` must be a real git repo:

```bash
cd demo-repo
git init -b main
git add .
git commit -m "demo baseline"
```

## 2. Start Backend With Real Claude Agent

```bash
cd backend
uv sync

export AGENT_GRAPH_DEMO_REPO_PATH="$(pwd)/../demo-repo"
export AGENT_GRAPH_ENABLE_REAL_RUNS=true
export ANTHROPIC_API_KEY="sk-..."

uv run uvicorn app.main:app --reload --port 8000
```

## 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## 4. Check Readiness

```bash
curl -s http://127.0.0.1:8000/api/v1/demo/status | jq
```

Proceed when `ready` is `true`.

## 5. Run The Demo

In the UI, create three branches from the hero task and watch them run.

CLI equivalent:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/branches/triple \
  -H "Content-Type: application/json" \
  -d '{"parent_id":"root","prompt":"Add rate limiting to POST /api/login","auto_run":true}' | jq
```

Watch events:

```bash
curl -N http://127.0.0.1:8000/api/v1/graph/sse
```

## 6. Inspect And Merge

```bash
curl -s http://127.0.0.1:8000/api/v1/nodes/<node-id>/diff | jq -r .diff
curl -s -X POST http://127.0.0.1:8000/api/v1/nodes/<node-id>/merge | jq
```

## 7. Reset Between Runs

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/demo/reset | jq
```

