"""
Per-node JSONL audit trail.

Each agent run writes one JSON object per line to
``<worktree>/.agent-graph/trace.jsonl``. The file is the single source of
truth for replay / debugging after the fact — easier to grep than terminal
logs, deterministic to parse.

Design notes:

- Best-effort: every disk failure is logged at WARNING and swallowed. The
  agent run must never be brought down by an audit-log write error.
- Append-only: existing lines are never rewritten, never rotated. The file
  is destroyed naturally when ``/api/v1/demo/reset`` deletes the worktree.
- Format: one ``GraphEvent`` (already JSON-serialisable via Pydantic) per
  line, separated by ``\\n``. Compatible with ``jq -c``, ``cat | python -c
  'json.loads'`` line-by-line, etc.
"""
from __future__ import annotations

import logging
from pathlib import Path

from ..models import GraphEvent

logger = logging.getLogger(__name__)

TRACE_DIRNAME = ".agent-graph"
TRACE_FILENAME = "trace.jsonl"


def trace_path(worktree_path: str | Path) -> Path:
    """Resolve the trace file path for a given worktree."""
    return Path(worktree_path) / TRACE_DIRNAME / TRACE_FILENAME


def write(worktree_path: str | Path, event: GraphEvent) -> None:
    """Append ``event`` as one JSON line. Never raises."""
    try:
        path = trace_path(worktree_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fp:
            fp.write(event.model_dump_json())
            fp.write("\n")
    except Exception as exc:  # noqa: BLE001 — audit log is best-effort by design
        logger.warning("audit_log write failed for %s: %s", worktree_path, exc)
