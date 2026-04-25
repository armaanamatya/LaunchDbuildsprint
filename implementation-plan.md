# Agent Graph - Implementation Plan

## Goal

Ship a hackathon-ready version of Agent Graph that proves one clear workflow:

1. Open a prepared local demo repo.
2. Spawn 2-3 agent branches on the same backend task.
3. Watch progress in a graph UI.
4. Compare results and diffs.
5. Merge the winning branch.

This document focuses on implementation order, ownership boundaries, and how to verify each step.

## Scope

### Phase 1: Hackathon MVP

Must prove:
- graph-based branching workflow
- local git worktrees
- Claude Agent SDK-powered node execution
- real-time progress streaming
- diff comparison
- merge winner into base branch

Explicitly not required:
- arbitrary repo import
- GitHub auth
- hosted multi-user architecture
- production-grade persistence
- PR creation
- PostHog-triggered execution
- multi-model support

### Phase 2: Product Expansion

Can add later:
- GitHub App integration
- hosted backend and workers
- Postgres and queueing
- PostHog-triggered issue packets
- PR workflows
- feature-flag rollout loops
- multiple issue sources

## Final Architecture for Phase 1

### Agent Graph App

- `Frontend`: React + TypeScript + Vite + Tailwind + `@xyflow/react` + Zustand
- `Backend`: FastAPI + asyncio
- `Agent runtime`: Claude Agent SDK
- `Git isolation`: git worktrees
- `Realtime`: SSE
- `App state`: in-memory first, optional SQLite later if needed

### Prepared Demo Repo

- `Frontend`: tiny React app
- `Backend`: small FastAPI app
- `DB`: SQLite
- `Tests`: pytest
- `Reset`: baseline reset script

### Why DB Is and Isn't Needed

For Agent Graph itself in Phase 1:
- a database is not strictly required
- in-memory state is acceptable for a local demo if the app can be restarted easily
- if time allows, use SQLite only for storing node metadata and run history

For the prepared demo repo:
- SQLite is required because the hero task should operate on a real-feeling app with seeded data

For PostHog:
- not required in Phase 1
- only needed for future signal-driven issue creation

## Suggested Repo Structure

```text
beatmyyeet/
  frontend/
  backend/
  demo-repo/
  plan.md
  suggestions.txt
  implementation-plan.md
```

Suggested backend structure:

```text
backend/
  app/
    main.py
    api.py
    models.py
    settings.py
    state.py
    events.py
    worktree.py
    diffing.py
    merge.py
    agent_runner/
      base.py
      claude_runner.py
      prompts.py
      hooks.py
    services/
      node_service.py
      repo_service.py
      eval_service.py
  tests/
```

Suggested frontend structure:

```text
frontend/
  src/
    App.tsx
    types.ts
    api/
    store/
    components/
      GraphView.tsx
      WorktreeNode.tsx
      AgentLogPanel.tsx
      DiffPanel.tsx
      ComparePanel.tsx
      Toolbar.tsx
      StatusBadge.tsx
    pages/
```

## Delivery Strategy

Build in vertical slices, not by isolated tech layer. Each slice should end with something visible and testable.

Recommended milestone order:

1. foundation and dev setup
2. prepared demo repo
3. backend worktree lifecycle
4. agent runner integration
5. SSE event stream
6. frontend graph shell
7. branch comparison UI
8. merge flow
9. polish and demo hardening

## Three-Person Work Split

This project should be divided by demo-critical ownership, not by equal-looking task piles.

### Person A - Armaan: Product, Demo, and Integration Lead

Primary mission:
- keep the team focused on the winning loop: branch, watch, compare, choose, merge
- protect the demo story from scope creep
- own the prepared hero task, final demo script, and integration checklist

Owns:
- final hero task wording
- demo repo reset flow and seed sanity checks
- acceptance criteria for the rate-limit task
- README/demo-day runbook
- final end-to-end rehearsal
- deciding which branch is the "winning" branch during the demo
- product polish decisions when tradeoffs come up

Concrete tasks:
- [ ] lock the hero prompt in `prompt.txt`
- [ ] verify the demo repo starts from a clean baseline
- [ ] make sure `scripts/reset_demo.py` reliably restores the demo repo
- [ ] write the 60-90 second spoken demo script
- [ ] maintain the final demo checklist
- [ ] run full rehearsals with backend and frontend together
- [ ] keep a fallback path ready if live agent execution fails

Tests/checks:
- [ ] from a clean checkout, run the reset script
- [ ] run demo repo tests
- [ ] run one full Agent Graph flow manually
- [ ] verify the product story is understandable without explaining implementation details first

### Person B - Abheeka: Backend, Git, and Agent Runtime Lead

Primary mission:
- make the backend reliably create isolated branches, run the agent, stream status, compute diffs, and merge the winner

Owns:
- FastAPI backend
- worktree lifecycle
- node/run state
- Claude Agent SDK runner or mock runner fallback
- SSE event stream
- diff endpoint
- merge endpoint
- backend tests

Concrete tasks:
- [ ] verify `GET /health`
- [ ] finish create/list/delete node APIs
- [ ] ensure each node maps to a real git worktree
- [ ] finish run-node lifecycle with mock runner first
- [ ] wire Claude Agent SDK behind the existing `AgentRunner` interface
- [ ] normalize runner output into graph events
- [ ] implement or harden diff capture
- [ ] implement or harden merge winner flow
- [ ] add clear errors for dirty repo, missing env vars, merge conflicts, and failed runs

Tests/checks:
- [ ] backend unit tests pass
- [ ] worktree tests pass using a temporary git repo
- [ ] mock runner can complete a run without an API key
- [ ] real runner smoke test works when `ANTHROPIC_API_KEY` is present
- [ ] diff endpoint returns readable output for a changed branch
- [ ] merge endpoint succeeds on a clean branch and explains conflicts

### Person C - Aayush: Frontend Graph and Comparison Lead

Primary mission:
- make the product feel like a new visual workflow, not a backend dashboard

Owns:
- React/Vite frontend
- graph canvas
- custom node UI
- toolbar/task input
- live status updates
- log panel
- diff/compare panel
- merge interaction
- visual polish and responsive layout

Concrete tasks:
- [ ] make root node plus child branches render clearly
- [ ] wire frontend API client to backend graph/node endpoints
- [ ] subscribe to SSE and update node state live
- [ ] build selected-node panel with logs and status
- [ ] build readable diff display
- [ ] build compare view for 2-3 completed branches
- [ ] add winner selection and merge button
- [ ] polish loading, empty, running, done, and error states
- [ ] check desktop and laptop-sized layouts for no overlap

Tests/checks:
- [ ] frontend builds successfully
- [ ] graph page renders without runtime errors
- [ ] create/run/merge controls call the correct endpoints
- [ ] SSE events update the graph without refresh
- [ ] diff and compare panels handle empty, loading, success, and error states

### Collaboration Contract

Shared contracts should be agreed early and changed rarely:
- node shape
- event payload shape
- status enum
- endpoint names
- branch naming convention
- demo repo path/env vars

Recommended shared status values:
- `idle`
- `creating`
- `running`
- `completed`
- `failed`
- `merged`

Recommended event names:
- `node_created`
- `node_status_changed`
- `agent_log`
- `tool_activity`
- `diff_ready`
- `agent_completed`
- `agent_failed`
- `branch_merged`

Daily integration rhythm:
- start by agreeing what each person will merge by the end of the session
- integrate at least once per day
- keep mock data and mock runner working even while real agent integration is in progress
- no one changes shared API/event contracts without telling the other two people

### Parallel Build Order

First parallel block:
- Armaan: lock demo script, prompt, and reset checklist
- Abheeka: make mock runner plus worktree lifecycle reliable
- Aayush: make graph shell consume mock graph data

Second parallel block:
- Armaan: rehearse the story against mock data and identify confusing UI moments
- Abheeka: add Claude Agent SDK and real SSE events
- Aayush: connect graph/log panels to live backend events

Third parallel block:
- Armaan: run full demo rehearsals and keep fallback branches ready
- Abheeka: harden diff, eval, merge, and reset flows
- Aayush: polish compare, merge, loading, and error states

### Handoff Rules

Backend to frontend:
- provide example JSON for every endpoint and event
- provide a mock runner path that does not need an API key
- provide predictable error messages the UI can display

Frontend to backend:
- provide exact fields needed for graph nodes, log entries, diffs, and merge state
- avoid inventing frontend-only statuses that the backend cannot produce

You to both:
- provide the final hero prompt
- define what counts as a successful demo
- make the final scope calls when time gets tight

### If Time Gets Tight

Cut in this order:
1. PostHog future work from the build.
2. Persistent DB for Agent Graph.
3. Fancy eval badges.
4. Delete-node UI.
5. Full arbitrary task input.

Do not cut:
- graph with 2-3 branches
- worktree-backed branch creation
- live progress or convincing simulated progress
- diff comparison
- winner merge or a clearly demonstrated merge fallback

## Milestone 0 - Setup and Contracts

### Tasks

- Create `frontend/` and `backend/` projects.
- Copy reusable `llm-canvas` ideas, not the entire app.
- Define shared node and event shapes before building UI behavior.
- Decide root branch naming and local worktree directory layout.
- Add `.env.example` for Agent Graph backend.
- Add `README` notes for local run commands.

### Frontend Needed

- Vite app scaffold
- Tailwind configured
- XYFlow dependency installed
- base layout and theme tokens

### Backend Needed

- FastAPI app scaffold
- settings loader
- basic API routing
- SSE response helper

### DB Needed

- none yet for Agent Graph

### PostHog Needed

- none

### Verification Checklist

- [ ] `frontend` starts with `npm run dev`
- [ ] `backend` starts with `uvicorn`
- [ ] health endpoint returns `200`
- [ ] one shared TypeScript/Python node shape is documented and stable

### Tests

- Backend:
  - [ ] smoke test for `GET /health`
- Frontend:
  - [ ] app shell renders without runtime errors

## Milestone 1 - Prepared Demo Repo

### Goal

Create the repo the agents will edit during the demo.

### Tasks

- Scaffold a tiny support inbox or issue tracker app.
- Include:
  - one auth-like endpoint
  - one list/search endpoint
  - one mutate endpoint
- Seed SQLite with realistic data.
- Add pytest coverage around the hero endpoint.
- Add reset script that restores clean baseline state.
- Add instructions for how Agent Graph points at this repo locally.

### Frontend Needed

- 2-3 minimal pages or screens
- enough UI to make the repo feel real

### Backend Needed

- FastAPI endpoints
- SQLite connection
- seed command or seed-on-start behavior

### DB Needed

- SQLite schema
- seed data

### PostHog Needed

- none

### Verification Checklist

- [ ] demo repo boots locally
- [ ] sample data is visible
- [ ] reset script returns repo to known clean state
- [ ] hero endpoint has passing tests

### Tests

- Demo repo:
  - [ ] endpoint tests for the hero route
  - [ ] seed data loads correctly
  - [ ] reset script works from dirty state

## Milestone 2 - Worktree Lifecycle Backend

### Goal

Make each graph node map to a real isolated branch/worktree.

### Tasks

- Implement repo configuration for the prepared repo path.
- Implement `create_worktree(base_branch, node_id)`.
- Implement `delete_worktree(node_id)`.
- Implement `get_diff(base_branch, branch_name)`.
- Implement `merge_branch(branch_name, target_branch)`.
- Persist runtime node state in memory.
- Expose API routes for:
  - create node
  - list nodes
  - delete node
  - fetch diff
  - merge node

### Frontend Needed

- none beyond basic API client stubs

### Backend Needed

- worktree service
- node service
- branch naming rules
- error handling around git failures

### DB Needed

- optional only
- if using SQLite for app metadata, store node id, branch name, path, status, created_at

### PostHog Needed

- none

### Verification Checklist

- [ ] creating a node creates a new worktree on disk
- [ ] node metadata returns from API
- [ ] deleting a node removes worktree and branch
- [ ] diff endpoint returns a git diff for changed branches
- [ ] merge endpoint merges branch into base branch

### Tests

- Backend:
  - [ ] unit tests for branch naming and worktree path generation
  - [ ] integration tests using a temporary git repo
  - [ ] merge success test
  - [ ] merge conflict handling test

## Milestone 3 - Claude Agent SDK Runner

### Goal

Run one Claude-powered coding session inside each worktree.

### Tasks

- Define internal `AgentRunner` interface.
- Implement `ClaudeAgentRunner`.
- Bind each run to `cwd=<node worktree path>`.
- Set safe `allowed_tools`.
- Set appropriate `permission_mode`.
- Add product-owned system prompt for coding nodes.
- Capture streamed SDK messages.
- Normalize raw SDK messages into app events.
- Record final result, status, and errors.

### Frontend Needed

- ability to trigger `run node`

### Backend Needed

- agent runner abstraction
- Claude Agent SDK integration
- hooks for audit/progress extraction
- background task management

### DB Needed

- none required
- optional run-history table if using SQLite

### PostHog Needed

- none

### Verification Checklist

- [ ] running a node starts a real agent session
- [ ] agent can read files in its worktree
- [ ] agent can edit files in its worktree
- [ ] agent can run allowed commands
- [ ] agent cannot escape intended tool policy
- [ ] completed run returns status and final diff

### Tests

- Backend:
  - [ ] unit test for event normalization from SDK messages
  - [ ] mock-runner test for job lifecycle
  - [ ] one real smoke test behind env flag, only if API key exists

## Milestone 4 - SSE and Run State

### Goal

Make node progress observable in real time.

### Tasks

- Implement global event stream for graph updates.
- Implement per-node event stream for logs and progress.
- Broadcast events on:
  - node created
  - node status changed
  - agent started
  - tool activity observed
  - diff ready
  - agent completed
  - agent failed
- Add heartbeat events.
- Add reconnection-safe frontend subscriptions.

### Frontend Needed

- SSE client hooks
- store updates from live events

### Backend Needed

- event dispatcher
- event payload schema

### DB Needed

- none

### PostHog Needed

- none

### Verification Checklist

- [ ] graph updates appear without refresh
- [ ] node status changes stream in real time
- [ ] logs stream while agent is running
- [ ] SSE reconnect does not break the page

### Tests

- Backend:
  - [ ] SSE event serialization tests
  - [ ] dispatcher queue tests
- Frontend:
  - [ ] store updates correctly when receiving node events

## Milestone 5 - Frontend Graph Shell

### Goal

Render the product's core visual surface.

### Tasks

- Build main page layout.
- Add graph canvas with root node.
- Add custom node component.
- Add node status visuals.
- Add toolbar for:
  - task input
  - new branch
  - run branch
  - merge winner
- Add selected-node side panel shell.

### Frontend Needed

- graph store
- XYFlow integration
- node layout
- selection handling
- polished visual states

### Backend Needed

- graph/list endpoints wired to UI

### DB Needed

- none

### PostHog Needed

- none

### Verification Checklist

- [ ] root node renders
- [ ] new child nodes appear in graph
- [ ] statuses are visually distinct
- [ ] selected node updates side panel
- [ ] UI still feels understandable with 3 active nodes

### Tests

- Frontend:
  - [ ] graph store add/select/update tests
  - [ ] component render tests for status badges
  - [ ] smoke test for graph page render

## Milestone 6 - Log, Diff, and Compare Experience

### Goal

Make the decision-making moment obvious.

### Tasks

- Build live log panel.
- Build diff panel with readable formatting.
- Build branch comparison view.
- Show lightweight evaluation signals if available.
- Add "winner" affordance in the UI.

### Frontend Needed

- diff rendering
- compare mode
- log viewer

### Backend Needed

- fresh diff endpoint
- optional eval endpoint/result structure

### DB Needed

- none

### PostHog Needed

- none

### Verification Checklist

- [ ] logs are readable while runs are active
- [ ] diff panel shows completed branch changes
- [ ] user can compare at least 2 branches clearly
- [ ] winning branch is obvious to select

### Tests

- Frontend:
  - [ ] diff panel handles empty diff, large diff, and error states
  - [ ] compare panel handles multiple finished nodes
- Backend:
  - [ ] diff endpoint returns expected content for changed branch

## Milestone 7 - Merge Flow

### Goal

Let the user pick a winner and merge confidently.

### Tasks

- Implement merge button flow.
- Add merge confirmation UI.
- Surface merge success/failure state.
- Refresh graph after merge.
- Optionally mark merged branches visually.

### Frontend Needed

- merge action
- success/error toasts or banners

### Backend Needed

- merge endpoint
- post-merge node/base refresh

### DB Needed

- none

### PostHog Needed

- none

### Verification Checklist

- [ ] merge action succeeds for clean branch
- [ ] merged result appears in base branch
- [ ] failed merge is explained to the user
- [ ] graph updates after merge

### Tests

- Backend:
  - [ ] merge endpoint success test
  - [ ] merge failure test
- Frontend:
  - [ ] merge action updates UI state correctly

## Milestone 8 - Evaluation and Demo Hardening

### Goal

Make the demo reliable enough to run repeatedly.

### Tasks

- Add optional "run tests" evaluation after agent completion.
- Show simple pass/fail evaluation badge.
- Add reset flow for demo repo and worktrees.
- Add seeded demo tasks.
- Add one-click local startup instructions.
- Add fallback states if an agent run fails.

### Frontend Needed

- evaluation badge
- reset action if exposed in UI

### Backend Needed

- eval service
- reset service

### DB Needed

- none

### PostHog Needed

- none

### Verification Checklist

- [ ] demo can be reset quickly between runs
- [ ] hero task succeeds often enough for live demo use
- [ ] failure mode still leaves a coherent product story
- [ ] one fallback demo branch can be precomputed if needed

### Tests

- Backend:
  - [ ] eval command output parsing test
  - [ ] reset command/service test

## Frontend Requirements Summary

### Core Pages

- graph page as the main product surface

### Components

- `GraphView`
- `WorktreeNode`
- `Toolbar`
- `StatusBadge`
- `AgentLogPanel`
- `DiffPanel`
- `ComparePanel`

### State

- nodes
- selected node
- active SSE subscriptions
- merge status
- diff cache

### Frontend Test Coverage

- store logic
- status rendering
- graph shell smoke test
- diff/compare empty and success states

## Backend Requirements Summary

### Core Services

- settings/config
- repo path management
- worktree lifecycle
- node state management
- Claude Agent SDK runner
- event dispatcher
- diff service
- merge service
- optional eval service

### Core Endpoints

- `GET /health`
- `GET /graph`
- `POST /nodes`
- `POST /nodes/{id}/run`
- `DELETE /nodes/{id}`
- `GET /nodes/{id}/diff`
- `POST /nodes/{id}/merge`
- `GET /graph/sse`
- `GET /nodes/{id}/sse`

### Backend Test Coverage

- temporary git repo integration tests
- node lifecycle tests
- merge tests
- SSE serialization tests
- agent runner normalization tests

## DB Requirements Summary

### Agent Graph App DB

Phase 1 recommendation:
- start with in-memory state

If persistence is needed without much complexity:
- use SQLite with tables for:
  - nodes
  - runs
  - events summary

### Prepared Demo Repo DB

Required:
- SQLite schema
- migration or init script
- seed data

### DB Verification

- [ ] schema creates cleanly
- [ ] seed data loads
- [ ] hero route behaves predictably against seed data

## PostHog Requirements Summary

### Phase 1

Not required.

### Phase 2

Add only after the core branch workflow works.

Needed pieces later:
- PostHog project and API key
- signal query or webhook ingestion layer
- issue packet generator
- evidence links stored with node/run metadata
- feature-flag rollout linkback

### PostHog Future Verification

- [ ] signal can be transformed into a structured issue packet
- [ ] issue packet can create one or more graph branches
- [ ] a fix can be linked back to the originating PostHog evidence

## Future Information Architecture

### Core Expansion Principle

As the product grows, it should not place every repo, issue, and branch on one giant graph.

The right model is layered:

- portfolio or workspace
- project
- issue or feature
- implementation branch
- agent run

### Recommended Hierarchy

```text
Workspace
  Project (repo)
    Issue/Feature
      Branch A
      Branch B
      Branch C
```

### Meaning of Each Layer

- `Workspace`
  - top-level collection of projects
  - useful for a user or team working across multiple repos

- `Project`
  - one repo and its active development surface
  - owns repo path, base branch, worktree root, and project settings

- `Issue/Feature`
  - one concrete problem to solve inside a project
  - may represent a prompt, GitHub issue, PostHog-derived issue packet, Linear ticket, or manual task

- `Implementation Branch`
  - one proposed approach for solving the issue
  - represented by a git branch plus worktree and a corresponding graph node

- `Agent Run`
  - one execution attempt on a branch
  - can include logs, tool activity, result summary, evals, and status

### UX Recommendation for the Future

Use separate surfaces for separate scopes:

- `Portfolio view`
  - shows multiple repos/projects and their active issue counts

- `Project view`
  - shows all active issues/features for one repo
  - can include status, priority, owner, and number of candidate branches

- `Issue graph view`
  - shows the detailed graph for one issue
  - this is where 2-3 implementation approaches are compared and chosen

This keeps the UI understandable as the number of repos and issues grows.

### System Design Implications

Each project should eventually have:
- its own clone path
- its own base branch
- its own worktree directory
- its own environment/configuration
- its own concurrency limits

Each issue should eventually have:
- issue id
- title
- summary or prompt
- origin source such as manual prompt, GitHub, Linear, or PostHog
- evaluation criteria
- status
- linked implementation branches

Each branch should eventually have:
- branch id
- git branch name
- worktree path
- parent issue id
- status
- diff summary
- eval results
- merge state

### Phase 1 Mapping

For the hackathon MVP, keep only the smallest slice of this model:

- one project
- one issue
- multiple implementation branches

That is enough to prove the long-term product structure without building the full multi-project system.

### Future Verification

- [ ] one workspace can contain multiple projects
- [ ] one project can contain multiple active issues
- [ ] one issue can contain multiple implementation branches
- [ ] issue and branch status can be understood without opening each graph
- [ ] the detailed issue graph still stays readable with multiple candidate approaches

## Environment Variables

### Agent Graph Backend

```bash
ANTHROPIC_API_KEY=
AGENT_GRAPH_DEMO_REPO_PATH=
AGENT_GRAPH_BASE_BRANCH=main
AGENT_GRAPH_WORKTREE_DIR=.agent-worktrees
AGENT_GRAPH_ENABLE_REAL_RUNS=true
```

### Optional Later

```bash
POSTHOG_PERSONAL_API_KEY=
POSTHOG_PROJECT_ID=
GITHUB_APP_ID=
GITHUB_APP_PRIVATE_KEY=
DATABASE_URL=
REDIS_URL=
```

## Recommended Acceptance Test for the Whole MVP

### End-to-End Flow

- [ ] open Agent Graph locally
- [ ] root node is visible
- [ ] create 3 child branches for the same hero task
- [ ] all 3 branches enter running state
- [ ] log activity streams for each branch
- [ ] at least 2 branches complete with readable diffs
- [ ] compare results side by side
- [ ] choose one branch
- [ ] merge winner into base branch
- [ ] reset demo state for another run

## Demo-Day Checklist

- [ ] demo repo seeded and clean
- [ ] all worktrees removed before starting
- [ ] env vars loaded
- [ ] Anthropic API key valid
- [ ] fallback precomputed branches available if live run fails
- [ ] hero prompt copied and ready
- [ ] one-sentence pitch memorized

## Recommended Build Order by Day

### Day 1

- setup
- demo repo
- worktree backend
- minimal graph shell

### Day 2

- Claude Agent SDK runner
- SSE
- log and diff UI
- merge flow

### Final Stretch

- eval badges
- visual polish
- reset flow
- demo rehearsal

## Bottom Line

Do not try to build every future system now.

Build the one loop that proves the product:
- branch
- watch
- compare
- choose
- merge
