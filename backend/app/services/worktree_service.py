from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..settings import get_settings


BRANCH_SEGMENT_PATTERN = re.compile(r"[^a-z0-9._/-]+")


class WorktreeError(Exception):
    """Raised when a git worktree operation fails."""


class MergeConflictError(WorktreeError):
    """Raised when a merge fails due to conflicts."""


def sanitize_branch_segment(value: str) -> str:
    normalized = value.strip().lower().replace(" ", "-")
    collapsed = BRANCH_SEGMENT_PATTERN.sub("-", normalized)
    collapsed = re.sub(r"-{2,}", "-", collapsed).strip("-/.")
    return collapsed or "node"


@dataclass(frozen=True)
class WorktreePlan:
    node_id: str
    parent_branch: str
    branch_name: str
    worktree_path: str
    implemented: bool = False


@dataclass(frozen=True)
class DiffSummary:
    files_changed: int
    insertions: int
    deletions: int


def _run_git(args: list[str], repo_path: Path) -> subprocess.CompletedProcess[str]:
    """Run a git command inside repo_path. Raises WorktreeError on failure."""
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise WorktreeError(
            f"git {args[0]} failed (rc={exc.returncode}): {exc.stderr.strip()}"
        ) from exc
    except FileNotFoundError as exc:
        raise WorktreeError("git executable not found on PATH") from exc


def _linked_worktree_paths(repo: Path) -> list[Path]:
    """Return absolute paths of every git-registered linked worktree (i.e.
    every worktree except the main one rooted at ``repo``)."""
    main = repo.resolve()
    result = _run_git(["worktree", "list", "--porcelain"], repo)
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            wt = Path(line[len("worktree ") :].strip()).resolve()
            if wt != main:
                paths.append(wt)
    return paths


def _dirty_paths_excluding_linked_worktrees(repo: Path) -> list[str]:
    """``git status --porcelain`` lines whose path lies *outside* any linked
    worktree.

    Linked worktrees naturally appear as untracked directories from the main
    worktree's perspective, but they are managed state — not stray dirtiness
    — so the strict-clean preflight should not block on them. Anything else
    (modified, staged, deleted, untracked outside worktrees) still blocks.
    """
    linked = _linked_worktree_paths(repo)
    status = _run_git(["status", "--porcelain"], repo)
    dirty: list[str] = []
    for line in status.stdout.splitlines():
        if len(line) < 4:
            continue
        path_str = line[3:].strip()
        # Strip trailing slash that git emits for fully-untracked directories.
        path_str = path_str.rstrip("/")
        if path_str.startswith('"') and path_str.endswith('"'):
            path_str = path_str[1:-1]
        full = (repo / path_str).resolve()
        # Three exclusion shapes for linked worktrees:
        #   1. full == wt: the entry IS a linked worktree directory itself
        #   2. wt in full.parents: entry is *inside* a linked worktree
        #   3. full in wt.parents: entry is an *ancestor* of a linked worktree
        #      (git reports just the bare intermediate dir when everything
        #       inside is itself a linked worktree)
        if any(
            full == wt or wt in full.parents or full in wt.parents for wt in linked
        ):
            continue
        dirty.append(line)
    return dirty


class WorktreeService:
    # ── naming helpers ────────────────────────────────────────────────────────

    def build_branch_name(self, parent_branch: str, node_id: str) -> str:
        # Use agent/ namespace to avoid git ref conflicts with the parent branch name.
        # e.g. parent=main, node=node-abc123 → agent/node-abc123
        node = sanitize_branch_segment(node_id)
        return f"agent/{node}"

    def build_worktree_path(self, branch_name: str) -> str:
        branch_leaf = sanitize_branch_segment(branch_name.replace("/", "-"))
        return str(Path(get_settings().worktree_root) / branch_leaf)

    def plan_worktree(self, node_id: str, parent_branch: str) -> WorktreePlan:
        branch_name = self.build_branch_name(parent_branch=parent_branch, node_id=node_id)
        return WorktreePlan(
            node_id=node_id,
            parent_branch=parent_branch,
            branch_name=branch_name,
            worktree_path=self.build_worktree_path(branch_name),
        )

    # ── repo path helper ──────────────────────────────────────────────────────

    def _get_repo_path(self, override: Path | str | None) -> Path:
        if override is not None:
            return Path(override)
        resolved = get_settings().resolved_demo_repo_path
        if not resolved:
            raise WorktreeError(
                "AGENT_GRAPH_DEMO_REPO_PATH is not configured and demo-repo was not found"
            )
        return Path(resolved)

    # ── git operations ────────────────────────────────────────────────────────

    def create_worktree(
        self,
        branch_name: str,
        worktree_path: str,
        parent_branch: str,
        repo_path: Path | str | None = None,
    ) -> None:
        """Create a new git branch and worktree at worktree_path.

        Refuses (raises ``WorktreeError``) when the demo repo has any
        uncommitted changes — modified files, staged changes, or untracked
        files. This is a deliberate strict-clean policy: agent worktrees
        must inherit a known-good state, and stray untracked files in the
        parent are the most common silent contaminant during rehearsals.
        Recover by committing, stashing, or ``POST /api/v1/demo/reset``.

        Raises a clearer message on branch-name collisions so demos surface
        ``run /api/v1/demo/reset`` as the action instead of raw git output.
        """
        repo = self._get_repo_path(repo_path)

        dirty = _dirty_paths_excluding_linked_worktrees(repo)
        if dirty:
            preview = ", ".join(line[3:].strip() for line in dirty[:5])
            raise WorktreeError(
                f"Demo repo has uncommitted changes (modified, staged, or untracked): {preview}. "
                "Commit, stash, or POST /api/v1/demo/reset first."
            )

        Path(worktree_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            _run_git(
                ["worktree", "add", "-b", branch_name, worktree_path, parent_branch],
                repo,
            )
        except WorktreeError as exc:
            if "already exists" in str(exc):
                raise WorktreeError(
                    f"{exc} (branch name collision; POST /api/v1/demo/reset to clear)"
                ) from exc
            raise

    def delete_worktree(
        self,
        worktree_path: str,
        branch_name: str,
        repo_path: Path | str | None = None,
    ) -> None:
        """Remove the worktree directory and delete the branch."""
        repo = self._get_repo_path(repo_path)

        # Remove the worktree (--force handles unclean state)
        try:
            _run_git(["worktree", "remove", "--force", worktree_path], repo)
        except WorktreeError:
            # Worktree may already be gone; prune stale entries
            try:
                _run_git(["worktree", "prune"], repo)
            except WorktreeError:
                pass

        # Delete the branch
        try:
            _run_git(["branch", "-D", branch_name], repo)
        except WorktreeError:
            pass  # Branch may already be gone or merged

    def get_diff(
        self,
        base_branch: str,
        branch_name: str,
        repo_path: Path | str | None = None,
    ) -> str:
        """Return the unified diff between base_branch and branch_name."""
        repo = self._get_repo_path(repo_path)
        result = _run_git(["diff", f"{base_branch}...{branch_name}"], repo)
        return result.stdout

    def get_diff_summary(
        self,
        base_branch: str,
        branch_name: str,
        repo_path: Path | str | None = None,
    ) -> DiffSummary:
        """Return file/insertion/deletion counts via ``git diff --numstat``.

        Uses git's own counts (not patch-text parsing) so renames, mode-only
        changes, and binary diffs are handled correctly. Binary files
        contribute to ``files_changed`` but not to insertion/deletion counts
        (git emits ``-`` instead of a number for binaries).
        """
        repo = self._get_repo_path(repo_path)
        result = _run_git(
            ["diff", "--numstat", f"{base_branch}...{branch_name}"], repo
        )
        files_changed = 0
        insertions = 0
        deletions = 0
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t", 2)
            if len(parts) < 3:
                continue
            ins_str, del_str, _path = parts
            files_changed += 1
            if ins_str.isdigit():
                insertions += int(ins_str)
            if del_str.isdigit():
                deletions += int(del_str)
        return DiffSummary(
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions,
        )

    def get_changed_files(
        self,
        base_branch: str,
        branch_name: str,
        repo_path: Path | str | None = None,
    ) -> list[str]:
        """Return paths of files changed between *base_branch* and *branch_name*.

        Uses ``git diff --name-only`` so renames and binary files are handled
        by git itself. Returns an empty list if the diff cannot be computed.
        """
        repo = self._get_repo_path(repo_path)
        try:
            result = _run_git(
                ["diff", "--name-only", f"{base_branch}...{branch_name}"], repo
            )
        except WorktreeError:
            return []
        return [line for line in result.stdout.splitlines() if line.strip()]

    def merge_branch(
        self,
        branch_name: str,
        target_branch: str,
        repo_path: Path | str | None = None,
    ) -> None:
        """Merge branch_name into target_branch (no-ff merge).

        Raises MergeConflictError if the merge has conflicts.
        The caller is responsible for ensuring the repo is on target_branch.
        """
        repo = self._get_repo_path(repo_path)

        # Verify we are on the target branch
        result = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo)
        current = result.stdout.strip()
        if current != target_branch:
            _run_git(["checkout", target_branch], repo)

        try:
            _run_git(["merge", "--no-ff", branch_name, "-m", f"Merge agent branch {branch_name}"], repo)
        except WorktreeError as exc:
            # Try to abort the failed merge to leave the repo clean
            try:
                _run_git(["merge", "--abort"], repo)
            except WorktreeError:
                pass
            raise MergeConflictError(
                f"Merge of {branch_name} into {target_branch} failed: {exc}"
            ) from exc


worktree_service = WorktreeService()
