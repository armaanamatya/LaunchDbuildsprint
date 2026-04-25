"""
Tests for ``WorktreeService.get_diff_summary`` (P2-I).

Critique #6: counting ``+``/``-`` lines in unified diff text breaks on
renames, binary files, and ``\\ No newline at end of file`` markers. We use
``git diff --numstat`` instead — git's own counts.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.services.worktree_service import (
    DiffSummary,
    WorktreeService,
)


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(
        ["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True
    )


@pytest.fixture
def repo_with_branch(tmp_path: Path) -> tuple[Path, str, str]:
    """Repo on `main` with a branch `feature` that has a commit."""
    _git(["init", "-b", "main"], tmp_path)
    _git(["config", "user.email", "t@t.test"], tmp_path)
    _git(["config", "user.name", "T"], tmp_path)
    (tmp_path / "kept.txt").write_text("first\nsecond\nthird\n")
    _git(["add", "."], tmp_path)
    _git(["commit", "-m", "init"], tmp_path)

    _git(["checkout", "-b", "feature"], tmp_path)
    return tmp_path, "main", "feature"


def test_summary_counts_simple_insertions(repo_with_branch: tuple[Path, str, str]) -> None:
    repo, base, branch = repo_with_branch
    (repo / "new.txt").write_text("alpha\nbeta\ngamma\n")
    _git(["add", "."], repo)
    _git(["commit", "-m", "add new"], repo)

    summary = WorktreeService().get_diff_summary(base, branch, repo_path=repo)
    assert summary == DiffSummary(files_changed=1, insertions=3, deletions=0)


def test_summary_counts_modifications(repo_with_branch: tuple[Path, str, str]) -> None:
    repo, base, branch = repo_with_branch
    (repo / "kept.txt").write_text("first\nALTERED\nthird\n")
    _git(["add", "."], repo)
    _git(["commit", "-m", "modify"], repo)

    summary = WorktreeService().get_diff_summary(base, branch, repo_path=repo)
    assert summary == DiffSummary(files_changed=1, insertions=1, deletions=1)


def test_summary_counts_multiple_files(repo_with_branch: tuple[Path, str, str]) -> None:
    repo, base, branch = repo_with_branch
    (repo / "a.txt").write_text("aaa\nbbb\n")
    (repo / "b.txt").write_text("ccc\n")
    (repo / "kept.txt").write_text("first\nsecond\nthird\nFOURTH\n")
    _git(["add", "."], repo)
    _git(["commit", "-m", "multi"], repo)

    summary = WorktreeService().get_diff_summary(base, branch, repo_path=repo)
    assert summary.files_changed == 3
    assert summary.insertions == 2 + 1 + 1
    assert summary.deletions == 0


def test_summary_handles_binary_files(repo_with_branch: tuple[Path, str, str]) -> None:
    """Binary files contribute to files_changed but not to ins/del counts."""
    repo, base, branch = repo_with_branch
    binary_data = bytes(range(256))
    (repo / "image.bin").write_bytes(binary_data)
    # Force git to treat as binary by adding to .gitattributes
    (repo / ".gitattributes").write_text("*.bin binary\n")
    _git(["add", "."], repo)
    _git(["commit", "-m", "add binary"], repo)

    summary = WorktreeService().get_diff_summary(base, branch, repo_path=repo)
    # 2 files: image.bin (binary) + .gitattributes (text)
    assert summary.files_changed == 2
    # Binary contributes 0 insertions; .gitattributes is 1 insertion
    assert summary.insertions == 1
    assert summary.deletions == 0


def test_summary_empty_when_no_diff(repo_with_branch: tuple[Path, str, str]) -> None:
    repo, base, branch = repo_with_branch
    summary = WorktreeService().get_diff_summary(base, branch, repo_path=repo)
    assert summary == DiffSummary(files_changed=0, insertions=0, deletions=0)
