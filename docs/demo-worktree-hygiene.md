# Demo worktree hygiene: why resets matter, and the contract

**Audience:** tech leads, backend owners, anyone running the Agent Graph demo or rehearsals.  
**Scope:** Stale git worktrees and non-baseline `main` after a run — the risk the analysis calls “worktree leaked from a prior rehearsal blocks fresh runs,” and the single pattern that fixes it.

---

## 1. Executive summary (30 seconds)

Each graph child node is a **real git worktree** plus an **`agent/*` branch** on the demo repository. Rehearsals that stop mid-flight, skip cleanup, or **merge a winner** leave **durable** git state: extra directories, branch refs, and often a different **`main`**. The next “fresh” demo is then **not** starting from the same world as the first — compare/diff/merge and the hero-task story break or confuse.

**Contract:** A full run or rehearsal **begins** with `POST /api/v1/demo/reset` (or equivalent runbook that invokes it). Reset restores the configured base branch to `AGENT_GRAPH_DEMO_BASELINE_REF`, cleans untracked dirt, and removes stale `agent/*` refs even after an API restart. No reset between runs = high risk; reset every time = boring and reliable.

---

## 2. Simple explanation (non-specialist)

Think of the demo as writing on a **shared whiteboard** (the `demo-repo`).

- Every time you “branch” in the app, the system **sticks extra sticky notes** on the board (worktrees) and **draws new lanes** (branches).
- If you run the story once and then start again **without erasing the board**, you are not looking at a clean “chapter 1” — you are looking at “chapter 1 plus whatever is still there.”
- Merging a winner is like **copying a lane into the main line**; the main line is no longer the same starting line for the next performance.

**The “elegant” fix is not more clever branching.** It is: **one button** that **erases the board and restores the official opening state** before each full rehearsal. In this codebase, that button is the **demo reset** endpoint, which clears disk, git, in-memory graph, and re-seeds the demo app data from the stored baseline ref.

---

## 3. Technical deep dive (what actually fails)

### 3.1 System model (accurate, not metaphor)

- `WorktreeService.create_worktree` runs `git worktree add -b <branch> <path> <parent>`.
- Paths live under `AGENT_GRAPH_DEMO_REPO_PATH` / `AGENT_GRAPH_WORKTREE_DIR` (e.g. `demo-repo/.agent-worktrees/...`).
- Branch names follow `agent/{sanitized-node-id}`; node IDs are unique per create, so **name collisions** are rare in normal use — but **cumulative** junk (leftover worktrees, stale refs, dirty `main`, merge residue) still poisons *repeatability* and can surface as:
  - **Dirty base:** `main` (or the configured base) has local changes; guards may reject new worktrees, or you compare against the wrong parent.
  - **Non-baseline `main`:** A prior merge means diffs, tests, and the “hero task” are no longer the same run-to-run.
  - **Operational confusion:** In-memory `graph_state` and browser UI can show “empty” after a process restart, while **git** still has old worktrees and `agent/*` — the *system of record* (git) disagrees with the *session* (RAM).

“Leak” here means: **artefacts of a previous rehearsal that were not removed by the same lifecycle that created them** — or **`main` not restored** after a merge. It is a **state hygiene** problem, not necessarily a single `git` error string.

### 3.2 Why this is a demo-killer, not a corner case

- The product story is **compare three branches, pick a winner, merge**. That story assumes a **known baseline** and **isolated** branch attempts.
- Rehearsal **without** reset trades determinism for speed; the failure shows up in **the narrative** (passing tests, diff shape, merge conflict) as much as in **raw errors**.

### 3.3 Related controls (complementary, not substitutes)

- **P2-style “dirty repo” preflight** before `git worktree add`: fail fast with a message that points to reset — good **when** someone skipped reset; does not replace **doing** the reset.
- **Idempotent** `POST /api/v1/demo/reset`: safe to run twice; supports “reset is the default, not the exception.”
- **Optional** `GET /api/v1/demo/status` (where implemented): single place to answer “is this host ready to demo?” (clean base, worktree count, key flags, eval/`uv` readiness).

---

## 4. The elegant solution (principal-level design)

**Principle:** *One idempotent, authoritative operation establishes the demo’s **initial world**.* Everything else (branch, run, diff, merge) is layered on that substrate.

### 4.1 The contract (non-negotiable for rehearsals)

| Rule | Rationale |
|------|-----------|
| **Every full end-to-end rehearsal** starts with `POST /api/v1/demo/reset` | Restores a single, known baseline: git, disk, in-memory graph, seed data. |
| **After any merge** you intend to undo for the next story | Reset (or explicitly accept a new baseline and update `AGENT_GRAPH_DEMO_BASELINE_REF`). |
| **Never assume** “the UI is empty” implies “the repo is clean” | **Git is durable;** the API process is not. |

### 4.2 What “reset” must cover (completeness)

1. **Process:** cancel or drain in-flight agent tasks so nothing writes mid-teardown.  
2. **Git + disk:** remove non-base worktrees, sweep all `agent/*` branches from git, prune, restore the configured base branch to `AGENT_GRAPH_DEMO_BASELINE_REF`, and run `git clean -fd` for untracked rehearsal dirt.  
3. **Data:** run the repo’s `scripts/reset_demo.py` (or equivalent) so app state (e.g. DB) matches the story.  
4. **Session:** graph state back to **root only** so UI and server agree.

If any step is missing, the next run is *partially* fresh — the worst class of bug: looks fine until the wrong moment on stage.

### 4.3 Operational excellence (boring is good)

- **Runbook:** one line, e.g. `curl -fsS -X POST http://127.0.0.1:8000/api/v1/demo/reset` before “open browser, click Branch×3.”
- **CI / smoke:** optional check that `demo/status` (if used) is green or that reset returns success after a synthetic dirty state.
- **On-call language:** if `create_worktree` or a run fails with “dirty / collision / weird git,” the first **support** step is **reset**, not ad-hoc `rm -rf` in `.agent-worktrees` (unless the runbook says so in emergency, and you understand git’s view).
- **Baseline caveat:** the baseline ref is created before backend-managed branch/merge operations. If a repo was already polluted before that ref existed, recreate the demo repo or explicitly repoint `AGENT_GRAPH_DEMO_BASELINE_REF` to the intended clean commit.

### 4.4 What we are *not* doing

- **Not** adding “smarter” leak detection in place of reset for normal operation — that increases branches and still leaves narrative drift (merged `main`).
- **Not** duplicating “cleanup” in three places; **one** reset path stays **canonical**.

---

## 5. Cross-references in this repository

- Risk row and mitigation: `analysis.md` §6 (worktree leaked… / `POST /api/v1/demo/reset`).
- Reset endpoint spec: `analysis.md` §4.2 item 9; implementation notes in `docs/person2.md` and `docs/plan-personB.md` (P2-C, P2-E).
- Implementation: `backend/app/api.py` — `demo_reset`; `backend/app/services/worktree_service.py` — worktree create/delete.
- Rehearsal habit: `analysis.md` §7 (reset between each rehearsal in the final stretch list).

---

## 6. One-line takeaway

**Reset is not a recovery tool; for rehearsals it is the first step of the program.**  
Treat it that way and the worktree “leak” class of issues stops being a principal-level fire drill and becomes a five-second habit.
