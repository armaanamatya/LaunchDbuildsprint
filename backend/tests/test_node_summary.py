"""
Tests for ``app.services.node_summary``.

The summary builder is deterministic: same inputs → same output. These
tests pin the boundary conditions described in the feature spec
(``docs/node-summary-feature-prompt.md``):

- passing eval + small diff → low risk, merge_candidate
- failing eval                → high risk, do_not_merge
- no eval                     → medium risk, needs_review
- no changed files            → high risk, do_not_merge
- large diff                  → medium risk
- ``write_summary`` produces valid JSON at the documented path
"""
from __future__ import annotations

import json
from pathlib import Path

from app.models import GraphNode, NodeDecisionSummary
from app.services.node_summary import (
    SUMMARY_DIRNAME,
    SUMMARY_FILENAME,
    build_decision_summary,
    write_summary,
)


def _node(status: str = "completed", strategy: str | None = "dependency") -> GraphNode:
    return GraphNode(
        id="node-test",
        label="Test branch",
        status=status,  # type: ignore[arg-type]
        branch_name="agent/node-test",
        worktree_path="/tmp/wt",
        parent_id="root",
        strategy=strategy,  # type: ignore[arg-type]
    )


def test_passing_eval_small_diff_is_merge_candidate() -> None:
    summary = build_decision_summary(
        node=_node(),
        diff_text="diff --git a b\n+x\n",
        changed_files=["app/main.py"],
        files_changed=1,
        insertions=10,
        deletions=2,
        tests_passed=4,
        tests_failed=0,
        test_summary="4 passed, 0 failed",
    )
    assert summary.risk == "low"
    assert summary.recommendation == "merge_candidate"
    assert summary.approach == "FastAPI dependency"


def test_failing_eval_is_do_not_merge() -> None:
    summary = build_decision_summary(
        node=_node(),
        diff_text="diff",
        changed_files=["app/main.py"],
        files_changed=1,
        insertions=5,
        deletions=0,
        tests_passed=2,
        tests_failed=3,
        test_summary="2 passed, 3 failed",
    )
    assert summary.risk == "high"
    assert summary.recommendation == "do_not_merge"
    assert any("failing test" in b.lower() for b in summary.review_focus)


def test_no_eval_data_yields_needs_review_medium_risk() -> None:
    summary = build_decision_summary(
        node=_node(),
        diff_text="diff",
        changed_files=["app/main.py"],
        files_changed=1,
        insertions=4,
        deletions=1,
        tests_passed=None,
        tests_failed=None,
        test_summary=None,
    )
    assert summary.risk == "medium"
    assert summary.recommendation == "needs_review"
    assert any("no eval" in b.lower() for b in summary.review_focus)


def test_no_changes_is_high_risk_do_not_merge() -> None:
    summary = build_decision_summary(
        node=_node(),
        diff_text="",
        changed_files=[],
        files_changed=0,
        insertions=0,
        deletions=0,
        tests_passed=None,
        tests_failed=None,
        test_summary=None,
    )
    assert summary.risk == "high"
    assert summary.recommendation == "do_not_merge"
    assert summary.headline == "No code changes detected"


def test_large_diff_is_medium_risk() -> None:
    summary = build_decision_summary(
        node=_node(),
        diff_text="x" * 1000,
        changed_files=[f"f{i}.py" for i in range(3)],
        files_changed=3,
        insertions=400,
        deletions=20,
        tests_passed=4,
        tests_failed=0,
        test_summary="4 passed, 0 failed",
    )
    assert summary.risk == "medium"
    # Still a merge candidate because tests pass — risk is advisory.
    assert summary.recommendation == "merge_candidate"


def test_failed_run_with_no_changes_explains_failure() -> None:
    summary = build_decision_summary(
        node=_node(status="failed"),
        diff_text="",
        changed_files=[],
        files_changed=0,
        insertions=0,
        deletions=0,
        tests_passed=None,
        tests_failed=None,
        test_summary=None,
    )
    assert summary.risk == "high"
    assert "failed" in summary.headline.lower() or "no code" in summary.headline.lower()


def test_zero_collected_tests_is_not_low_risk() -> None:
    """passed=0, failed=0 means pytest collected nothing — not a green check."""
    summary = build_decision_summary(
        node=_node(),
        diff_text="diff",
        changed_files=["app/main.py"],
        files_changed=1,
        insertions=3,
        deletions=0,
        tests_passed=0,
        tests_failed=0,
        test_summary="no tests collected",
    )
    assert summary.risk == "medium"
    assert summary.recommendation == "needs_review"
    assert any("collected no tests" in b.lower() for b in summary.review_focus)


def test_diff_unavailable_yields_honest_summary() -> None:
    """When diff data cannot be computed, summary must not claim 'no changes'."""
    summary = build_decision_summary(
        node=_node(),
        diff_text="",
        changed_files=[],
        files_changed=0,
        insertions=0,
        deletions=0,
        tests_passed=4,
        tests_failed=0,
        test_summary="4 passed, 0 failed",
        diff_unavailable=True,
    )
    assert summary.risk == "medium"
    assert summary.recommendation == "needs_review"
    assert "unavailable" in summary.headline.lower()
    assert any("diff data unavailable" in b.lower() for b in summary.review_focus)


def test_write_summary_produces_valid_json(tmp_path: Path) -> None:
    summary = build_decision_summary(
        node=_node(),
        diff_text="diff",
        changed_files=["app/main.py"],
        files_changed=1,
        insertions=2,
        deletions=0,
        tests_passed=1,
        tests_failed=0,
        test_summary="1 passed, 0 failed",
    )
    write_summary(str(tmp_path), summary)
    written = tmp_path / SUMMARY_DIRNAME / SUMMARY_FILENAME
    assert written.exists()
    payload = json.loads(written.read_text())
    # Round-trip through the model so schema drift breaks the test, not silently passes.
    NodeDecisionSummary.model_validate(payload)
    assert payload["risk"] == "low"
    assert payload["recommendation"] == "merge_candidate"


def test_write_summary_swallows_filesystem_errors(tmp_path: Path) -> None:
    """A bad worktree path must never raise — agent runs depend on it."""
    summary = build_decision_summary(
        node=_node(),
        diff_text="",
        changed_files=[],
        files_changed=0,
        insertions=0,
        deletions=0,
        tests_passed=None,
        tests_failed=None,
        test_summary=None,
    )
    bogus = tmp_path / "missing-file.txt"
    bogus.write_text("blocking file")
    # Path that resolves through a *file*, not a directory — mkdir will fail.
    write_summary(str(bogus / "nope"), summary)
