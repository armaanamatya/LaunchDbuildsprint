"""
Integration tests for WorktreeService git operations.
Uses a real temporary git repo — no mocking.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.services.worktree_service import (
    MergeConflictError,
    WorktreeError,
    WorktreeService,
    sanitize_branch_segment,
)


# ── helpers ───────────────────────────────────────────────────────────────────


def git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """Minimal git repo with one commit on main."""
    git(["init", "-b", "main"], tmp_path)
    git(["config", "user.email", "test@agent-graph.test"], tmp_path)
    git(["config", "user.name", "Agent Graph Test"], tmp_path)
    (tmp_path / "README.md").write_text("# test repo")
    git(["add", "."], tmp_path)
    git(["commit", "-m", "init"], tmp_path)
    return tmp_path


@pytest.fixture()
def svc() -> WorktreeService:
    return WorktreeService()


# ── sanitize_branch_segment ───────────────────────────────────────────────────


def test_sanitize_strips_special_chars() -> None:
    assert sanitize_branch_segment("Feature Branch #1") == "feature-branch-1"


def test_sanitize_collapses_dashes() -> None:
    assert sanitize_branch_segment("a--b---c") == "a-b-c"


def test_sanitize_empty_fallback() -> None:
    assert sanitize_branch_segment("!!!") == "node"


# ── build_branch_name / build_worktree_path ───────────────────────────────────


def test_build_branch_name_shape(svc: WorktreeService) -> None:
    name = svc.build_branch_name("main", "node-abc123")
    assert name == "agent/node-abc123"


def test_build_branch_name_sanitizes_inputs(svc: WorktreeService) -> None:
    name = svc.build_branch_name("Main Branch", "node:42")
    assert name == "agent/node-42"


# ── create_worktree ───────────────────────────────────────────────────────────


def test_create_worktree_creates_directory_and_branch(
    svc: WorktreeService, git_repo: Path, tmp_path: Path
) -> None:
    worktree_path = tmp_path / "worktrees" / "test-node"

    svc.create_worktree(
        branch_name="agent/test-node",
        worktree_path=str(worktree_path),
        parent_branch="main",
        repo_path=git_repo,
    )

    assert worktree_path.exists(), "Worktree directory should be created"
    branches = git(["branch"], git_repo)
    assert "agent/test-node" in branches


def test_create_worktree_inherits_parent_content(
    svc: WorktreeService, git_repo: Path, tmp_path: Path
) -> None:
    worktree_path = tmp_path / "worktrees" / "content-check"

    svc.create_worktree(
        branch_name="agent/content",
        worktree_path=str(worktree_path),
        parent_branch="main",
        repo_path=git_repo,
    )

    assert (worktree_path / "README.md").exists(), "Worktree should inherit parent files"


def test_create_worktree_raises_on_invalid_repo(
    svc: WorktreeService, tmp_path: Path
) -> None:
    not_a_repo = tmp_path / "not-a-repo"
    not_a_repo.mkdir()

    with pytest.raises(WorktreeError):
        svc.create_worktree(
            branch_name="agent/x",
            worktree_path=str(tmp_path / "wt"),
            parent_branch="main",
            repo_path=not_a_repo,
        )


# ── delete_worktree ───────────────────────────────────────────────────────────


def test_delete_worktree_removes_directory_and_branch(
    svc: WorktreeService, git_repo: Path, tmp_path: Path
) -> None:
    worktree_path = tmp_path / "worktrees" / "to-delete"

    svc.create_worktree(
        branch_name="agent/to-delete",
        worktree_path=str(worktree_path),
        parent_branch="main",
        repo_path=git_repo,
    )
    assert worktree_path.exists()

    svc.delete_worktree(
        worktree_path=str(worktree_path),
        branch_name="agent/to-delete",
        repo_path=git_repo,
    )

    assert not worktree_path.exists(), "Worktree directory should be removed"
    branches = git(["branch"], git_repo)
    assert "agent/to-delete" not in branches


def test_delete_worktree_is_idempotent(
    svc: WorktreeService, git_repo: Path, tmp_path: Path
) -> None:
    """Calling delete on an already-deleted worktree should not raise."""
    worktree_path = tmp_path / "worktrees" / "idempotent"

    svc.create_worktree(
        branch_name="agent/idempotent",
        worktree_path=str(worktree_path),
        parent_branch="main",
        repo_path=git_repo,
    )
    svc.delete_worktree(
        worktree_path=str(worktree_path),
        branch_name="agent/idempotent",
        repo_path=git_repo,
    )
    # Second delete should not raise
    svc.delete_worktree(
        worktree_path=str(worktree_path),
        branch_name="agent/idempotent",
        repo_path=git_repo,
    )


# ── get_diff ──────────────────────────────────────────────────────────────────


def test_get_diff_returns_empty_for_unmodified_branch(
    svc: WorktreeService, git_repo: Path, tmp_path: Path
) -> None:
    worktree_path = tmp_path / "worktrees" / "diff-empty"
    svc.create_worktree(
        branch_name="agent/diff-empty",
        worktree_path=str(worktree_path),
        parent_branch="main",
        repo_path=git_repo,
    )

    diff = svc.get_diff("main", "agent/diff-empty", repo_path=git_repo)
    assert diff == "", "Unmodified branch should produce an empty diff"


def test_get_diff_returns_changes_after_commit(
    svc: WorktreeService, git_repo: Path, tmp_path: Path
) -> None:
    worktree_path = tmp_path / "worktrees" / "diff-changes"
    svc.create_worktree(
        branch_name="agent/diff-changes",
        worktree_path=str(worktree_path),
        parent_branch="main",
        repo_path=git_repo,
    )

    # Make a change in the worktree
    (worktree_path / "new_file.py").write_text("# added by agent\n")
    git(["add", "."], worktree_path)
    git(["config", "user.email", "test@test.com"], worktree_path)
    git(["config", "user.name", "Test"], worktree_path)
    git(["commit", "-m", "agent adds file"], worktree_path)

    diff = svc.get_diff("main", "agent/diff-changes", repo_path=git_repo)
    assert "new_file.py" in diff
    assert "+# added by agent" in diff


# ── merge_branch ──────────────────────────────────────────────────────────────


def test_merge_branch_integrates_changes_into_target(
    svc: WorktreeService, git_repo: Path, tmp_path: Path
) -> None:
    worktree_path = tmp_path / "worktrees" / "merge-ok"
    svc.create_worktree(
        branch_name="agent/merge-ok",
        worktree_path=str(worktree_path),
        parent_branch="main",
        repo_path=git_repo,
    )

    # Commit a change on the agent branch
    (worktree_path / "merged_file.py").write_text("# merged\n")
    git(["add", "."], worktree_path)
    git(["config", "user.email", "test@test.com"], worktree_path)
    git(["config", "user.name", "Test"], worktree_path)
    git(["commit", "-m", "agent: add merged_file"], worktree_path)

    svc.merge_branch("agent/merge-ok", "main", repo_path=git_repo)

    # The file should now be on main
    assert (git_repo / "merged_file.py").exists()


def test_merge_branch_raises_on_conflict(
    svc: WorktreeService, git_repo: Path, tmp_path: Path
) -> None:
    # Create two branches that both modify the same line
    wt_a = tmp_path / "worktrees" / "conflict-a"
    wt_b = tmp_path / "worktrees" / "conflict-b"

    svc.create_worktree("agent/conflict-a", str(wt_a), "main", repo_path=git_repo)
    svc.create_worktree("agent/conflict-b", str(wt_b), "main", repo_path=git_repo)

    def configure_git(path: Path) -> None:
        git(["config", "user.email", "test@test.com"], path)
        git(["config", "user.name", "Test"], path)

    configure_git(wt_a)
    configure_git(wt_b)

    # Branch A writes line version A to the same file
    (wt_a / "conflict.py").write_text("x = 'version A'\n")
    git(["add", "."], wt_a)
    git(["commit", "-m", "branch A changes conflict.py"], wt_a)

    # Merge A into main so main has the file
    svc.merge_branch("agent/conflict-a", "main", repo_path=git_repo)

    # Branch B was created before A was merged, so it also has a conflicting version
    (wt_b / "conflict.py").write_text("x = 'version B'\n")
    git(["add", "."], wt_b)
    git(["commit", "-m", "branch B changes conflict.py"], wt_b)

    with pytest.raises(MergeConflictError):
        svc.merge_branch("agent/conflict-b", "main", repo_path=git_repo)


# ── strict-clean preflight (P2-E) ─────────────────────────────────────────────


def test_create_worktree_blocks_on_modified_file(svc: WorktreeService, git_repo: Path) -> None:
    """A modified-but-uncommitted file must block worktree creation."""
    (git_repo / "README.md").write_text("# locally modified\n")

    with pytest.raises(WorktreeError) as exc_info:
        svc.create_worktree(
            branch_name="agent/should-fail",
            worktree_path=str(git_repo / "wt"),
            parent_branch="main",
            repo_path=git_repo,
        )
    msg = str(exc_info.value)
    assert "uncommitted" in msg.lower()
    assert "/api/v1/demo/reset" in msg


def test_create_worktree_blocks_on_untracked_file(svc: WorktreeService, git_repo: Path) -> None:
    """Strict-clean policy: even untracked files block creation (per docstring)."""
    (git_repo / "untracked.txt").write_text("just sitting here\n")

    with pytest.raises(WorktreeError) as exc_info:
        svc.create_worktree(
            branch_name="agent/should-also-fail",
            worktree_path=str(git_repo / "wt2"),
            parent_branch="main",
            repo_path=git_repo,
        )
    assert "uncommitted" in str(exc_info.value).lower()


def test_create_worktree_branch_collision_message_points_to_reset(
    svc: WorktreeService, git_repo: Path
) -> None:
    """Branch-name collision should mention /api/v1/demo/reset as the cure."""
    svc.create_worktree(
        branch_name="agent/collision",
        worktree_path=str(git_repo / "wt-first"),
        parent_branch="main",
        repo_path=git_repo,
    )
    with pytest.raises(WorktreeError) as exc_info:
        svc.create_worktree(
            branch_name="agent/collision",
            worktree_path=str(git_repo / "wt-second"),
            parent_branch="main",
            repo_path=git_repo,
        )
    assert "/api/v1/demo/reset" in str(exc_info.value)
