from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..settings import get_settings


@dataclass(frozen=True)
class RepoConfigSnapshot:
    repo_path: str | None
    repo_exists: bool
    git_dir_exists: bool
    base_branch: str
    worktree_root: str
    worktree_root_exists: bool


class RepoService:
    def get_repo_config(self) -> RepoConfigSnapshot:
        settings = get_settings()
        repo_path = Path(settings.resolved_demo_repo_path) if settings.resolved_demo_repo_path else None
        git_dir = repo_path / ".git" if repo_path else None
        worktree_root = Path(settings.worktree_root)

        return RepoConfigSnapshot(
            repo_path=str(repo_path) if repo_path else None,
            repo_exists=bool(repo_path and repo_path.exists()),
            git_dir_exists=bool(git_dir and git_dir.exists()),
            base_branch=settings.base_branch,
            worktree_root=str(worktree_root),
            worktree_root_exists=worktree_root.exists(),
        )


repo_service = RepoService()

