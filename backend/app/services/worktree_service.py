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
        """Create a new git branch and worktree at worktree_path."""
        repo = self._get_repo_path(repo_path)
        Path(worktree_path).parent.mkdir(parents=True, exist_ok=True)
        _run_git(
            ["worktree", "add", "-b", branch_name, worktree_path, parent_branch],
            repo,
        )

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
