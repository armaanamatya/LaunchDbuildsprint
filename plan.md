# Agent Graph - Revised Hackathon Plan

## Thesis

Code quality is becoming commoditized. The moat is idea, design, and decision-making.

Agent Graph should not be framed as "another AI coding app." It should be framed as a branching workspace for software decisions:

Instead of asking one agent for one answer, we let you explore multiple implementation paths, compare them visually, and merge the best one.

## What We Are Actually Building

We are building a graph-based coding interface where each node is a real git worktree plus an isolated coding agent.

For the hackathon, the product must prove one unforgettable loop:

1. Open one prepared repo.
2. Show a root node representing the current codebase or starting task.
3. Create 2-3 child agent branches from the same task.
4. Stream each branch's progress in real time.
5. Compare the resulting diffs side by side.
6. Choose one winner and merge it.

That is enough to prove the thesis.

## Rubric Strategy

### Idea

Primary story:
- Real coding work is not linear.
- Existing AI coding tools force one path at a time.
- Agent Graph turns multiple implementation paths into a visible, explorable workspace.

Why this can score well:
- The graph metaphor is legible.
- The problem is easy to understand.
- The interaction maps to real engineering behavior: branch, compare, choose, merge.

### Functionality

We should optimize for one reliable demo loop, not a broad platform.

That means:
- no arbitrary repo selection for the hackathon demo
- no broad auth complexity in the first version
- no PR creation
- no multi-model routing
- no production-grade persistence requirements
- no team collaboration requirements

### UI/UX

The graph must be the hero, not a side panel.

Design goals:
- light theme first
- editorial, product-forward feel
- restrained color system with one strong accent
- highly readable node states: idle, running, done, error
- clear branch comparison
- confident merge action
- avoid generic purple-gradient AI dashboard styling

### Presentation

The demo should be:

1. Coding is not linear.
2. Current tools force one path at a time.
3. We built a branching workspace where each node is a real implementation path.
4. Here is one task explored three ways.
5. Here is why one branch wins.
6. One click merges the winner.

The presentation should focus on product insight, not infrastructure.

## Decision Log

### Q1. Is this local-only, or should it support hosted use?

Answer:
- We do want a hosted private alpha eventually.
- For the actual product direction, this is a private alpha architecture problem, not an all-on-Vercel production problem.

Clarification:
- User count is not the main constraint.
- The real constraint is architecture: persistent repos, git worktrees, long-running agents, state, and safe command execution.

### Q2. Should we split the architecture into Vercel frontend plus separate backend/workers?

Answer:
- Yes.

Recommended architecture:
- frontend: Vercel
- backend API and workers: always-on container or VM service such as Railway, Fly.io, Render, or a VPS
- state: Postgres at minimum
- queue: Redis/Upstash or a DB-backed job table
- auth for hosted use: GitHub App preferred over broad OAuth repo scope

Hackathon clarification:
- This hosted architecture is the future product direction.
- The hackathon demo does not need to fully implement all of it.

### Q3. What is the hero use case in the demo?

Answer:
- Primary hero use case: multiple implementations of the same feature
- Secondary expansion story: managing many active branches across different features

Why:
- "Three agents tried three ways to solve the same task" is instantly understandable.
- It makes the compare-and-merge moment obvious.
- It proves why the graph matters.

Expansion story:
- Once the comparison workflow is proven, the same graph becomes the management surface for many active agent branches across a project.

### Q4. Should the demo run on an arbitrary repo/task or a prepared one?

Answer:
- Prepared repo plus preselected task.

Why:
- more reliable
- easier to keep the demo legible
- easier to guarantee different but valid implementations
- easier to reset between runs

### Q5. Should the hero task be backend-first or frontend-first?

Answer:
- Backend-first.

Why:
- more deterministic for agents
- easier to validate with tests
- cleaner diffs
- easier to create multiple plausible implementations
- the Agent Graph product UI already carries the visual wow factor

### Q6. What is the right demo substrate?

Answer:
- A purpose-built simple local web app.

Not recommended:
- generic script repo
- arbitrary external repo
- remote app that must be deployed during the demo

Recommended substrate:
- frontend: tiny React app
- backend: small FastAPI app
- db: SQLite with seeded data
- tests: pytest suite
- reset: one script that restores a known baseline

### Q7. What is a hero task?

Answer:
- The hero task is the one carefully chosen coding problem used in the demo to prove the product.

It must be:
- small enough to finish reliably
- real enough to matter
- open-ended enough for multiple valid implementations
- different enough that the branch comparison is visually obvious

Bad hero tasks:
- vague prompts like "improve the app"
- giant feature requests
- tasks where all branches look almost identical

## Prepared Demo Repo

### Recommended Repo Shape

Build a tiny full-stack app that feels real but stays small.

Recommended concept:
- a lightweight support inbox or issue tracker

Why this works:
- judges immediately understand the app
- it gives the backend real product context
- it supports multiple good backend hero tasks

### Stack

- frontend: React
- backend: FastAPI
- database: SQLite
- tests: pytest
- seed data: included
- reset script: included

### Scope

Keep the repo intentionally small:
- 2-3 screens
- 3-5 backend endpoints
- one auth-like endpoint
- one list or search endpoint
- one mutate endpoint such as reply, resolve, archive, or comment

## Recommended Hero Task Direction

### Best Task Family

Backend tasks with 2-3 plausible implementation strategies:
- add rate limiting to an endpoint
- add caching to a summary or search endpoint
- refactor auth middleware

### Strongest Default Recommendation

If we need a default hero task, use:

`Add rate limiting to a real API endpoint in the prepared app.`

Good endpoint choices:
- `POST /api/login`
- `POST /api/tickets/{id}/reply`

Why this is strong:
- easy to explain
- meaningful in a real app
- multiple valid implementation paths
- easy to compare in diffs
- easy to validate with tests

### Example Branch Strategies

For a rate-limiting hero task, the branches could naturally differ like this:
- Branch A: route-local implementation
- Branch B: shared dependency or decorator
- Branch C: reusable middleware or utility-backed implementation

## Product Scope for the Hackathon MVP

### Must Ship

- Graph UI with root node plus child branches
- Create 2-3 agent branches from one task
- Per-node status: idle, running, done, error
- Streaming agent logs
- Side-by-side diff comparison
- Winner selection
- Merge winner into the base branch

### Strongly Optional

- simple evaluation signal after each run, such as tests passing or failing
- local reset button or script for repeated demos

### Explicitly Out of Scope

- arbitrary repo picker
- hosted multi-user production architecture
- full GitHub auth and repo import flow
- pull request creation
- multi-model orchestration
- team collaboration
- persistent multi-session storage

## Localhost Execution Model

### How the Demo Runs Locally

The browser is only the control surface. The actual coding agent does not run in the browser.

Recommended local architecture:
- frontend runs locally and renders the graph UI
- FastAPI backend runs locally and owns all agent execution
- prepared demo repo is cloned locally in a known path
- each graph node maps to a real git worktree under that repo

### Local Execution Flow

1. The user opens Agent Graph in the browser.
2. The frontend sends a create-node request to the local FastAPI backend.
3. The backend creates a new git worktree for that node.
4. The backend starts an async agent job for the node.
5. That agent runs with its working directory set to the node's worktree.
6. As the agent reads files, edits code, and runs commands, the backend streams progress events to the frontend over SSE.
7. When the agent finishes, the backend captures:
   - final status
   - diff against the base branch
   - optional test results
   - any error details
8. The frontend lets the user compare branches and merge the chosen winner.

### Worktree Layout

Example structure:

```text
demo-repo/
  .agent-worktrees/
    node-a/
    node-b/
    node-c/
```

Each worktree is isolated so branches can modify code independently without stepping on each other.

## Agent Runtime Choice

### Revised Recommendation

For the hackathon MVP, we should strongly prefer the Claude Agent SDK for Anthropic-powered nodes instead of building a custom low-level tool loop first.

### Why the Claude Agent SDK Fits Phase 1

The current Agent SDK already provides most of what this product needs:
- built-in agent loop
- built-in file editing and command execution tools
- working-directory scoping via `cwd`
- permissions and allow/deny tool controls
- hooks for logging and guardrails
- sessions and continuity
- real-time streamed messages for progress UIs
- support for `.claude/` project configuration and skills

### Why We Did Not Assume It at the Very Beginning

The original plan leaned toward a custom tool loop because that gives:
- model-agnostic control
- exact control over tool definitions and UI semantics
- easier future support for non-Anthropic models behind one internal abstraction

That is still a valid long-term architecture.

However, for the hackathon, those benefits are less important than shipping speed and reliability. A custom loop is more engineering work and creates more places for bugs in:
- tool execution
- turn handling
- streaming
- permissions
- retries
- context/session management

### Final Runtime Recommendation

Phase 1:
- use the Claude Agent SDK as the execution engine for Anthropic-powered branches
- wrap it in our own node/job abstraction so the UI and backend are still product-owned

Phase 2 and beyond:
- introduce an internal agent adapter layer if we want multiple providers
- keep the graph, worktree lifecycle, diffs, evals, and merge workflow provider-agnostic

This gives us the best of both worlds:
- fastest path to a strong demo now
- cleaner path to multi-model support later

### Suggested Phase 1 Runtime Shape

- backend creates one agent session per node
- each session runs with `cwd` set to the node's worktree path
- allowed tools are tightly scoped for coding tasks
- permission mode is set to a controlled mode appropriate for headless execution
- hooks are used for audit logging, progress extraction, and policy checks
- streamed SDK messages are translated into SSE events for the frontend

### How We Keep It Custom While Using the Agent SDK

Using the Agent SDK does not mean the product becomes a thin wrapper.

We still own the parts that matter most to the user experience:
- graph orchestration and node lifecycle
- git worktree creation, deletion, diffing, and merge flows
- branch comparison UX
- winner selection and merge gating
- evaluation pipeline
- issue packet generation
- audit logs and product-level permissions
- the exact SSE event model exposed to the frontend

The Agent SDK should be treated as the execution engine inside each node, not the product itself.

### Customization Surface

Ways to make the runtime product-specific while still using the SDK:
- wrap the SDK behind our own internal `AgentRunner` interface
- define product-owned system prompts for each node type
- use hooks for logging, tool filtering, and policy enforcement
- add MCP servers or custom tools for GitHub, PostHog, Linear, Jira, or internal services
- define subagents for specialized tasks such as testing, code review, or summarization
- use project skills and `.claude/` configuration where helpful
- normalize SDK message streams into our own node events such as `agent_started`, `tool_called`, `tests_passed`, `diff_ready`, and `agent_failed`

### Long-Term Architecture Note

If we later want multi-model support, the abstraction boundary should sit above the SDK.

That means:
- the product owns a provider-agnostic node/job model
- Anthropic-backed nodes can use the Agent SDK
- other providers can use a different runner implementation later
- the graph UI, worktree lifecycle, evals, and merge workflow remain unchanged

## UX Principles

- The graph is the product.
- Nodes should feel alive while running.
- Comparison must be obvious without explanation.
- The merge action should feel decisive and satisfying.
- The interface should emphasize decisions, not controls and configuration.

## Demo Script

1. Explain the problem: coding is branching work, but AI tools are mostly linear.
2. Open the prepared repo in Agent Graph.
3. Show the root node.
4. Launch 2-3 child branches on the same backend task.
5. Let the audience watch the branches stream progress.
6. Compare the resulting diffs.
7. Explain why one branch is best.
8. Merge the winner.
9. Close with the expansion story: the same graph can later manage many concurrent branches across a real project.

## Score Target

If we execute the narrowed plan well, the realistic target is:

- Idea: 7.5/8
- Functionality: 4/5
- UI/UX: 3.5-4/4
- Presentation: 2.5-3/3

## Future Architecture

### Product Direction

The long-term vision is bigger than prompt-driven branching.

In the future, branches should be able to start from real product signals and engineering workflows, not just manual prompts.

### Signal Sources

Potential future issue sources:
- PostHog analytics signals
- user feedback submissions
- GitHub issues
- Linear or Jira tickets
- failing tests or regressions
- production alerts

### Example PostHog Flow

One compelling future workflow:

1. PostHog detects friction such as funnel dropoff, rage clicks, repeated failures, or abnormal behavior.
2. A triage service converts that signal into a structured engineering issue.
3. Agent Graph creates a branch or set of branches for that issue.
4. Coding agents attempt fixes in isolated worktrees.
5. Tests and evaluations run on each branch.
6. The best candidate becomes a PR or merge recommendation.
7. A human reviews and approves the final change.

### PostHog Expansion Architecture

Recommended future pipeline:
- product telemetry captured in PostHog
- triage service queries or receives issue-relevant signals
- triage service produces a structured issue packet
- Agent Graph opens one or more branches from that packet
- coding agents attempt fixes in isolated worktrees
- evaluations run
- output becomes a PR, merge recommendation, or flagged experiment candidate

### Structured Issue Packet

For signal-driven branches, the branch input should not just be raw analytics.

It should be a structured issue packet with fields like:
- title
- summary of the user problem
- affected route or feature
- evidence links such as replay URLs or issue links
- suspected files or service area
- severity and confidence
- evaluation criteria for a successful fix

### Product-Safe Rollout

PostHog also makes the release side stronger.

Future rollout pattern:
- use PostHog analytics and error tracking to identify problems
- use Agent Graph to generate candidate fixes
- ship the winning fix behind a feature flag when appropriate
- use PostHog again to observe whether the fix improves outcomes

This closes the loop from:
signal -> branch -> fix -> rollout -> measurement

### Why This Fits Agent Graph

- It turns the product from prompt-only coding into signal-driven execution.
- It gives branches a concrete origin in real product problems.
- It reinforces the core thesis: software decisions should be visible, comparable, and reviewable.

### Future Guardrails

This should not mean uncontrolled autonomous pushes to production.

Recommended guardrails:
- never write directly to main by default
- create branches or PRs first
- run tests and lightweight evaluations
- preserve human approval before merge
- log the signal, prompt, agent actions, and diff for auditability

## Official Sources Reviewed

The following official docs informed the current plan and architecture decisions:

### Anthropic

- Agent SDK overview: https://code.claude.com/docs/en/agent-sdk/overview
- How the agent loop works: https://code.claude.com/docs/en/agent-sdk/agent-loop
- Python SDK reference: https://platform.claude.com/docs/en/agent-sdk/python
- Permissions: https://code.claude.com/docs/en/agent-sdk/permissions

Used for:
- deciding that Phase 1 should prefer the Agent SDK
- confirming built-in tools, hooks, sessions, subagents, MCP, and `cwd` support
- confirming the SDK can stream messages suitable for SSE-backed progress UIs

### GitHub

- Differences between GitHub Apps and OAuth apps: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps
- Deciding when to build a GitHub App: https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/deciding-when-to-build-a-github-app
- Scopes for OAuth apps: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps

Used for:
- preferring GitHub Apps over OAuth apps for the future hosted product
- understanding why broad OAuth scopes are a poor long-term fit

### Vercel

- FastAPI on Vercel: https://vercel.com/docs/frameworks/backend/fastapi
- Vercel Functions: https://vercel.com/docs/functions
- Configuring maximum duration for Vercel Functions: https://vercel.com/docs/functions/configuring-functions/duration

Used for:
- deciding not to make the core worker architecture all-on-Vercel
- separating the future hosted architecture into Vercel frontend plus always-on backend/workers

### PostHog

- Product analytics: https://posthog.com/docs/product-analytics
- Session replay: https://posthog.com/docs/session-replay
- Error tracking: https://posthog.com/docs/error-tracking
- API overview: https://posthog.com/docs/api
- Feature flags: https://posthog.com/docs/feature-flags

Used for:
- shaping the future signal-driven branch architecture
- validating that PostHog can provide analytics, replay, errors, APIs, and rollout support for future issue-triggered agent flows

## Bottom Line

Ship one unforgettable branching workflow.

Do not spend the hackathon proving that the platform can do everything.
Spend the hackathon proving that the graph changes how coding decisions are made.
