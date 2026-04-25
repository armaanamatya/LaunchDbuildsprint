from __future__ import annotations

import asyncio
import logging
import subprocess
from collections.abc import AsyncGenerator
from pathlib import Path

from .base import AgentRunner, NormalizedEvent

logger = logging.getLogger(__name__)

# Rate limiting implementation written by the mock agent.

_RATE_LIMIT_MODULE = '''\
"""In-memory IP-based rate limiter for POST /api/login.

Written by mock agent. Branch A strategy: route-local counter.
"""
from __future__ import annotations

import time
from collections import defaultdict

MAX_ATTEMPTS: int = 5
WINDOW_SECONDS: int = 60

_store: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(ip: str) -> int | None:
    """Return retry-after seconds if the IP is rate-limited, else None.

    Counts every call (successful or not) toward the limit.
    """
    now = time.time()
    cutoff = now - WINDOW_SECONDS
    _store[ip] = [t for t in _store[ip] if t > cutoff]
    if len(_store[ip]) >= MAX_ATTEMPTS:
        retry_after = int(WINDOW_SECONDS - (now - _store[ip][0])) + 1
        return max(1, retry_after)
    _store[ip].append(now)
    return None
'''

# Snippet inserted at the top of the login handler body
_LOGIN_RATE_LIMIT_GUARD = '''\
        from .rate_limit import check_rate_limit
        _client_ip = (request.client.host if request.client else None) or "unknown"
        _retry_after = check_rate_limit(_client_ip)
        if _retry_after is not None:
            raise HTTPException(
                status_code=429,
                detail="Too many login attempts. Please try again later.",
                headers={"Retry-After": str(_retry_after)},
            )
'''

# The exact line in main.py that starts the login handler body
_LOGIN_BODY_ANCHOR = "        agent = get_agent_by_email(request.app.state.db_path, payload.email)"


def _apply_rate_limiting(worktree_path: str) -> bool:
    """Patch app/main.py with rate limiting. Returns True on success."""
    wt = Path(worktree_path)
    main_py = wt / "app" / "main.py"

    if not main_py.exists():
        return False

    source = main_py.read_text(encoding="utf-8")

    # Idempotency guard
    if "check_rate_limit" in source:
        return True

    if _LOGIN_BODY_ANCHOR not in source:
        logger.warning("Mock runner: could not find login anchor in %s", main_py)
        return False

    patched = source.replace(
        _LOGIN_BODY_ANCHOR,
        _LOGIN_RATE_LIMIT_GUARD + _LOGIN_BODY_ANCHOR,
        1,
    )
    main_py.write_text(patched, encoding="utf-8")

    rate_limit_py = wt / "app" / "rate_limit.py"
    rate_limit_py.write_text(_RATE_LIMIT_MODULE, encoding="utf-8")
    return True


def _git_commit(worktree_path: str, message: str) -> None:
    """Commit all changes in the worktree. Silently skips on error."""
    kwargs: dict = dict(cwd=worktree_path, check=True, capture_output=True, text=True)
    try:
        subprocess.run(["git", "config", "user.email", "mock-agent@agent-graph.test"], **kwargs)
        subprocess.run(["git", "config", "user.name", "Mock Agent (Agent Graph)"], **kwargs)
        subprocess.run(["git", "add", "-A"], **kwargs)
        subprocess.run(["git", "commit", "-m", message], **kwargs)
    except subprocess.CalledProcessError as exc:
        logger.warning("Mock runner git commit failed: %s", exc.stderr.strip())


class MockAgentRunner(AgentRunner):
    """Simulates an agent run without calling the LLM API.

    Used when AGENT_GRAPH_ENABLE_REAL_RUNS=false (the default).
    Writes a real rate-limiting implementation to the worktree so that
    the diff and merge flows work end-to-end during demos.
    """

    async def stream(
        self,
        node_id: str,
        prompt: str,
        worktree_path: str,
    ) -> AsyncGenerator[NormalizedEvent, None]:
        wt = Path(worktree_path)

        yield NormalizedEvent(type="agent_started", node_id=node_id)
        await asyncio.sleep(0.3)

        yield NormalizedEvent(
            type="agent_text",
            node_id=node_id,
            content="Reading the repository structure to understand the codebase...",
        )
        await asyncio.sleep(0.6)

        yield NormalizedEvent(
            type="agent_tool_use",
            node_id=node_id,
            tool_name="Read",
            tool_input={"file_path": "app/main.py"},
        )
        await asyncio.sleep(0.5)

        yield NormalizedEvent(
            type="agent_tool_use",
            node_id=node_id,
            tool_name="Read",
            tool_input={"file_path": "tests/test_rate_limit.py"},
        )
        await asyncio.sleep(0.4)

        yield NormalizedEvent(
            type="agent_text",
            node_id=node_id,
            content=(
                "I can see the login endpoint at POST /api/login. "
                "The acceptance tests expect HTTP 429 with a Retry-After header after 5 attempts per IP. "
                "I will implement an in-memory per-IP counter approach."
            ),
        )
        await asyncio.sleep(0.8)

        # Apply the actual implementation
        success = _apply_rate_limiting(worktree_path)

        if success:
            yield NormalizedEvent(
                type="agent_tool_use",
                node_id=node_id,
                tool_name="Write",
                tool_input={"file_path": "app/rate_limit.py", "description": "New in-memory rate limit module"},
            )
            await asyncio.sleep(0.4)

            yield NormalizedEvent(
                type="agent_tool_use",
                node_id=node_id,
                tool_name="Edit",
                tool_input={"file_path": "app/main.py", "description": "Add rate limit guard to POST /api/login"},
            )
            await asyncio.sleep(0.6)

            yield NormalizedEvent(
                type="agent_text",
                node_id=node_id,
                content="Running the rate-limit acceptance tests to verify the implementation...",
            )
            await asyncio.sleep(0.4)

            yield NormalizedEvent(
                type="agent_tool_use",
                node_id=node_id,
                tool_name="Bash",
                tool_input={"command": "uv run pytest tests/test_rate_limit.py -v"},
            )
            await asyncio.sleep(1.2)

            yield NormalizedEvent(
                type="agent_tool_use",
                node_id=node_id,
                tool_name="Bash",
                tool_input={"command": "git add -A && git commit -m 'agent: add in-memory rate limiting to POST /api/login'"},
            )

            _git_commit(worktree_path, "agent: add in-memory rate limiting to POST /api/login")
            await asyncio.sleep(0.3)

            yield NormalizedEvent(
                type="agent_completed",
                node_id=node_id,
                content=(
                    "Implementation complete. Added app/rate_limit.py with an in-memory per-IP counter "
                    "and patched the login handler to return HTTP 429 with Retry-After after 5 attempts. "
                    "All 4 acceptance tests pass."
                ),
            )
        else:
            # Worktree is not a PulseDesk repo; write a placeholder.
            placeholder = wt / "agent_notes.md"
            placeholder.write_text(
                "# Mock Agent Notes\n\nThis worktree does not contain a PulseDesk app.\n"
                "The mock agent would implement rate limiting on `POST /api/login` here.\n"
            )
            _git_commit(worktree_path, "agent: placeholder implementation notes")

            yield NormalizedEvent(
                type="agent_completed",
                node_id=node_id,
                content="Mock run complete (placeholder; worktree is not a PulseDesk repo).",
            )
