"""
Deterministic per-node decision summary.

Builds a ``NodeDecisionSummary`` from already-collected diff and eval data.
No LLM calls — fast, stable, and demo-safe. The rules are intentionally
transparent so the UI can be honest about *why* a branch is risky.

Like ``audit_log.write``, ``write_summary`` is best-effort: a missing
worktree, a permission error, or a serialization failure must never crash an
agent run. Callers should treat exceptions raised here as advisory.
"""
from __future__ import annotations

import logging
from pathlib import Path

from ..models import (
    GraphNode,
    NodeDecisionSummary,
    SummaryRecommendation,
    SummaryRisk,
)

logger = logging.getLogger(__name__)

SUMMARY_DIRNAME = ".agent-graph"
SUMMARY_FILENAME = "summary.json"

# Cap for review_focus and (visible) changed_files. Full file list is preserved
# in the JSON sidecar; the model object also carries the full list — the cap
# below applies only to review_focus bullets.
_MAX_REVIEW_FOCUS = 4
_LARGE_DIFF_LINES = 300
_MEDIUM_FILES = 5

# Common high-signal paths a reviewer should look at first. Order matters:
# the first match wins so we don't spam the focus list with overlapping hits.
_CRITICAL_PATTERNS: tuple[tuple[str, str], ...] = (
    ("app/main.py", "Touches FastAPI app entrypoint (app/main.py)"),
    ("middleware", "Adds or modifies middleware"),
    ("dependencies", "Adds or modifies request dependencies"),
    ("settings", "Touches settings/config"),
    ("auth", "Touches auth code"),
)


def _approach_label(strategy: str | None) -> str:
    if strategy == "route_local":
        return "Route-local guard"
    if strategy == "dependency":
        return "FastAPI dependency"
    if strategy == "middleware":
        return "ASGI middleware"
    return "Custom branch"


def _headline(
    *,
    node: GraphNode,
    files_changed: int,
    has_changes: bool,
    tests_failed: int | None,
    diff_unavailable: bool,
) -> str:
    # Order matters — most specific signal wins.
    if tests_failed and tests_failed > 0:
        return f"{_approach_label(node.strategy)} — tests failing"
    if node.status == "failed":
        return "Run failed before producing a mergeable change"
    if diff_unavailable:
        return "Diff unavailable — review branch manually"
    if not has_changes or files_changed == 0:
        return "No code changes detected"
    # Keep the prompt out of the headline (it is rendered separately and may
    # be long). The approach + a noun the user can scan is enough.
    return f"Adds rate limiting with a {_approach_label(node.strategy).lower()}"


def _classify_risk(
    *,
    has_changes: bool,
    files_changed: int,
    insertions: int,
    deletions: int,
    tests_passed: int | None,
    tests_failed: int | None,
    eval_ran: bool,
    node_status: str,
    diff_unavailable: bool,
) -> tuple[SummaryRisk, str]:
    # Ordering reflects signal strength: failing tests / failed run trump the
    # data-gap markers (diff_unavailable, missing eval). Otherwise a node with
    # red tests and a transient git failure could be reported as merely
    # "medium — Diff data unavailable", hiding the real problem.
    if tests_failed is not None and tests_failed > 0:
        return "high", f"{tests_failed} test(s) failing"
    if node_status == "failed":
        return "high", "Agent run failed"
    if not diff_unavailable and node_status == "completed" and not has_changes:
        return "high", "Agent completed but produced no changes"
    if diff_unavailable:
        return "medium", "Diff data unavailable"
    if not eval_ran or tests_passed is None:
        return "medium", "No eval data — tests were not run"
    # tests_passed == 0 with tests_failed == 0 means pytest collected nothing —
    # not a green check. Treat as no meaningful eval signal.
    if tests_passed == 0 and (tests_failed or 0) == 0:
        return "medium", "Eval ran but collected no tests"
    diff_lines = insertions + deletions
    if files_changed > _MEDIUM_FILES:
        return "medium", f"Touches {files_changed} files"
    if diff_lines > _LARGE_DIFF_LINES:
        return "medium", f"Large diff ({diff_lines} lines)"
    return "low", "Tests pass and diff is small"


def _classify_recommendation(
    *,
    has_changes: bool,
    tests_passed: int | None,
    tests_failed: int | None,
    diff_unavailable: bool,
) -> SummaryRecommendation:
    if tests_failed is not None and tests_failed > 0:
        return "do_not_merge"
    if diff_unavailable:
        return "needs_review"
    if not has_changes:
        return "do_not_merge"
    if tests_passed is not None and tests_passed > 0 and (tests_failed or 0) == 0:
        return "merge_candidate"
    return "needs_review"


def _review_focus(
    *,
    changed_files: list[str],
    files_changed: int,
    insertions: int,
    deletions: int,
    tests_passed: int | None,
    tests_failed: int | None,
    eval_ran: bool,
    diff_unavailable: bool,
) -> list[str]:
    bullets: list[str] = []
    if tests_failed and tests_failed > 0:
        bullets.append(f"{tests_failed} failing test(s) — inspect before merge")
    if not eval_ran:
        bullets.append("No eval ran — verify behavior manually")
    elif (tests_passed or 0) == 0 and (tests_failed or 0) == 0:
        bullets.append("Eval ran but collected no tests")
    if diff_unavailable:
        bullets.append("Diff data unavailable — verify changes from git directly")
    diff_lines = insertions + deletions
    if files_changed > _MEDIUM_FILES:
        bullets.append(f"Diff spans {files_changed} files")
    elif diff_lines > _LARGE_DIFF_LINES:
        bullets.append(f"Large diff ({diff_lines} lines)")

    seen_patterns: set[str] = set()
    for path in changed_files:
        lower = path.lower()
        for needle, message in _CRITICAL_PATTERNS:
            if needle in lower and message not in seen_patterns:
                bullets.append(message)
                seen_patterns.add(message)
                break
        if len(bullets) >= _MAX_REVIEW_FOCUS:
            break

    return bullets[:_MAX_REVIEW_FOCUS]


def build_decision_summary(
    *,
    node: GraphNode,
    diff_text: str,
    changed_files: list[str],
    files_changed: int,
    insertions: int,
    deletions: int,
    tests_passed: int | None,
    tests_failed: int | None,
    test_summary: str | None,
    diff_unavailable: bool = False,
) -> NodeDecisionSummary:
    """Build a deterministic ``NodeDecisionSummary`` from collected run data.

    ``diff_text`` is currently unused at the data level (counts come from
    git --numstat), but is part of the API so future heuristics can inspect
    patch content without a re-fetch. ``diff_unavailable`` distinguishes
    "agent produced no changes" (legitimate finding) from "we could not
    compute a diff" (data gap) so the summary stays honest in either case.
    """
    has_changes = bool(diff_text and diff_text.strip()) or files_changed > 0
    eval_ran = tests_passed is not None or tests_failed is not None

    headline = _headline(
        node=node,
        files_changed=files_changed,
        has_changes=has_changes,
        tests_failed=tests_failed,
        diff_unavailable=diff_unavailable,
    )
    risk, risk_reason = _classify_risk(
        has_changes=has_changes,
        files_changed=files_changed,
        insertions=insertions,
        deletions=deletions,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        eval_ran=eval_ran,
        node_status=node.status,
        diff_unavailable=diff_unavailable,
    )
    recommendation = _classify_recommendation(
        has_changes=has_changes,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        diff_unavailable=diff_unavailable,
    )
    focus = _review_focus(
        changed_files=changed_files,
        files_changed=files_changed,
        insertions=insertions,
        deletions=deletions,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        eval_ran=eval_ran,
        diff_unavailable=diff_unavailable,
    )
    return NodeDecisionSummary(
        headline=headline,
        approach=_approach_label(node.strategy),
        changed_files=changed_files,
        files_changed=files_changed,
        insertions=insertions,
        deletions=deletions,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        test_summary=test_summary,
        risk=risk,
        risk_reason=risk_reason,
        recommendation=recommendation,
        review_focus=focus,
    )


def write_summary(worktree_path: str | Path, summary: NodeDecisionSummary) -> None:
    """Write *summary* as JSON to ``<worktree>/.agent-graph/summary.json``.

    Best-effort: every failure is logged at WARNING and swallowed, mirroring
    ``audit_log.write``. Summary generation must never break a successful run.
    """
    try:
        path = Path(worktree_path) / SUMMARY_DIRNAME / SUMMARY_FILENAME
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 — best-effort by design
        logger.warning("node_summary write failed for %s: %s", worktree_path, exc)
