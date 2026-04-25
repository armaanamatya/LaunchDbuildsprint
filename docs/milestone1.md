# Milestone 1 — Prepared Demo Repo

## What this is

PulseDesk is a tiny support inbox app purpose-built for Agent Graph demos.
It is the repo the coding agents will edit during the live demo.

The hero task: **add rate limiting to `POST /api/login`**.
Each agent branch will implement it differently. The 4 failing acceptance tests define exactly what "done" looks like.

---

## What was built

### App — `demo-repo/app/`

| File | What it does |
|---|---|
| `main.py` | FastAPI app factory (`create_app`). Mounts routes, templates, static files. |
| `db.py` | SQLite schema, seed data, `ensure_database`, `reset_database`. |
| `repository.py` | All SQL queries: login lookup, ticket list/search, ticket detail, add reply, dashboard stats. |
| `schemas.py` | Pydantic models for all request/response shapes. |
| `security.py` | SHA-256 password hashing, token generation (demo-grade). |

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/login` | Auth-like endpoint. **Hero task target.** |
| `GET` | `/api/tickets` | List/search tickets. Supports `?q=` and `?status=`. |
| `GET` | `/api/tickets/{id}` | Ticket detail with messages. |
| `POST` | `/api/tickets/{id}/reply` | Add a reply, update ticket status. |
| `GET` | `/api/dashboard` | Aggregate stats + recent tickets. |
| `GET` | `/` | HTML dashboard (Jinja2). |
| `GET` | `/inbox` | HTML inbox with search (Jinja2). |
| `GET` | `/tickets/{id}` | HTML ticket detail (Jinja2). |

### Seeded data

- 4 agents (`alex`, `priya`, `jordan`, `sam`) — `sam` is inactive for negative-path tests
- 6 tickets across billing, platform, authentication, product queues
- 12 messages across the tickets
- All passwords: `demo123`

### Reset script — `demo-repo/scripts/reset_demo.py`

Deletes the SQLite file and recreates it from the seed data. Safe to run repeatedly.

### Tests — `demo-repo/tests/`

| File | Tests | Status |
|---|---|---|
| `test_login.py` | Login success, wrong password, inactive user, ticket search, reset flow | 5 pass |
| `test_rate_limit.py` | Rate limit threshold, 429 response, Retry-After header, successful logins count, email rotation bypass | 4 fail (hero task not yet implemented) |

The 4 failing tests are intentional. They are the acceptance criteria for the hero task. Agent branches must make them pass.

---

## How to run

```bash
cd demo-repo
uv sync
uv run uvicorn app.main:app --reload --port 8010
```

Open:

- Dashboard: http://127.0.0.1:8010/
- Inbox: http://127.0.0.1:8010/inbox
- API docs: http://127.0.0.1:8010/docs

---

## How to test

```bash
cd demo-repo
uv run pytest -v
```

Expected output:

```
tests/test_login.py::test_login_returns_access_token_for_seeded_agent     PASSED
tests/test_login.py::test_login_rejects_invalid_password                  PASSED
tests/test_login.py::test_login_rejects_inactive_user                     PASSED
tests/test_login.py::test_seeded_ticket_search_returns_known_results      PASSED
tests/test_login.py::test_reset_database_restores_known_baseline          PASSED
tests/test_rate_limit.py::test_login_allows_attempts_under_the_limit      PASSED
tests/test_rate_limit.py::test_login_returns_429_after_limit_exceeded     FAILED  <- hero task
tests/test_rate_limit.py::test_rate_limit_response_includes_retry_after_header FAILED  <- hero task
tests/test_rate_limit.py::test_successful_login_counts_toward_rate_limit  FAILED  <- hero task
tests/test_rate_limit.py::test_rate_limit_applies_regardless_of_email     FAILED  <- hero task

6 passed, 4 failed
```

---

## How to reset

```bash
cd demo-repo
uv run python scripts/reset_demo.py
```

Drops and recreates the database. Run this between demo takes to restore the clean baseline.

---

## Git setup

The demo-repo has its own git history so Agent Graph can create worktrees from it:

```
demo-repo/
  .git/          <- standalone repo, branch: main
  .gitignore     <- excludes .venv/, data/, __pycache__/
```

Agent Graph worktrees will live at `demo-repo/.agent-worktrees/` (gitignored).

---

## Agent Graph integration

The backend auto-detects the demo-repo if it is at `../demo-repo` relative to the backend.
To point it at a different path, set:

```bash
AGENT_GRAPH_DEMO_REPO_PATH=/absolute/path/to/demo-repo
```

---

## Hero task prompt (for agents)

> Add rate limiting to `POST /api/login`. Allow a maximum of 5 login attempts per IP address within a 60-second window. Return HTTP 429 with a `Retry-After` header when the limit is exceeded. Successful logins count toward the limit. Run `uv run pytest tests/test_rate_limit.py` to verify.

---

## Verification checklist

- [x] Demo repo boots locally
- [x] Sample data visible on dashboard and inbox
- [x] Reset script restores clean baseline from dirty state
- [x] 5 baseline tests pass
- [x] 4 rate-limit acceptance tests fail correctly (hero task pending)
- [x] Repo has its own git history on `main` branch ready for worktrees
- [x] Agent Graph integration documented
