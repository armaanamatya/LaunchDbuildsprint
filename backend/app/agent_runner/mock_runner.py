from __future__ import annotations

import asyncio
import logging
import subprocess
from collections.abc import AsyncGenerator
from pathlib import Path

from .base import AgentRunner, NormalizedEvent, StrategyHint

logger = logging.getLogger(__name__)


# ── Strategy A: route-local counter ─────────────────────────────────────────────

_RATE_LIMIT_MODULE_ROUTE_LOCAL = '''\
"""In-memory IP-based rate limiter for POST /api/login.

Strategy A — route-local counter. The login handler imports check_rate_limit
and calls it inline. Simplest, smallest diff.
"""
from __future__ import annotations

import time
from collections import defaultdict

MAX_ATTEMPTS: int = 5
WINDOW_SECONDS: int = 60

_store: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(ip: str) -> int | None:
    """Return retry-after seconds if the IP is rate-limited, else None.

    Counts every call (successful or not) toward the limit so that successful
    logins cannot be used to enumerate valid credentials.
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

_LOGIN_BODY_ANCHOR = "        agent = get_agent_by_email(request.app.state.db_path, payload.email)"

_LOGIN_RATE_LIMIT_GUARD_ROUTE_LOCAL = '''\
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


# ── Strategy B: FastAPI dependency ──────────────────────────────────────────────

_RATE_LIMIT_MODULE_DEPENDENCY = '''\
"""IP-based rate limiter exposed as a FastAPI dependency.

Strategy B — Depends(enforce_login_rate_limit). The login handler stays
clean; the dependency owns the policy and raises HTTPException directly.
"""
from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request

MAX_ATTEMPTS: int = 5
WINDOW_SECONDS: int = 60

_store: dict[str, list[float]] = defaultdict(list)


def _check(ip: str) -> int | None:
    now = time.time()
    cutoff = now - WINDOW_SECONDS
    _store[ip] = [t for t in _store[ip] if t > cutoff]
    if len(_store[ip]) >= MAX_ATTEMPTS:
        retry_after = int(WINDOW_SECONDS - (now - _store[ip][0])) + 1
        return max(1, retry_after)
    _store[ip].append(now)
    return None


async def enforce_login_rate_limit(request: Request) -> None:
    """Raise 429 with Retry-After if the calling IP has exceeded the window."""
    ip = (request.client.host if request.client else None) or "unknown"
    retry_after = _check(ip)
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
'''

_LOGIN_SIGNATURE_ANCHOR = (
    "    async def login(payload: LoginRequest, request: Request) -> LoginResponse:"
)
_LOGIN_SIGNATURE_PATCHED_DEPENDENCY = (
    "    async def login(\n"
    "        payload: LoginRequest,\n"
    "        request: Request,\n"
    "        _rl: None = Depends(enforce_login_rate_limit),\n"
    "    ) -> LoginResponse:"
)


# ── Strategy C: ASGI middleware ─────────────────────────────────────────────────

_RATE_LIMIT_MODULE_MIDDLEWARE = '''\
"""IP-based rate limiter implemented as Starlette middleware.

Strategy C — RateLimitMiddleware filters POST /api/login at the ASGI layer.
The login handler is left untouched; policy lives outside the route.
"""
from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

MAX_ATTEMPTS: int = 5
WINDOW_SECONDS: int = 60

_store: dict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP fixed-window limiter for POST /api/login."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "POST" and request.url.path == "/api/login":
            ip = (request.client.host if request.client else None) or "unknown"
            now = time.time()
            cutoff = now - WINDOW_SECONDS
            _store[ip] = [t for t in _store[ip] if t > cutoff]
            if len(_store[ip]) >= MAX_ATTEMPTS:
                retry_after = max(1, int(WINDOW_SECONDS - (now - _store[ip][0])) + 1)
                return JSONResponse(
                    {"detail": "Too many login attempts. Please try again later."},
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                )
            _store[ip].append(now)
        return await call_next(request)
'''

_APP_FACTORY_ANCHOR = (
    '    app = FastAPI(\n'
    '        title="PulseDesk Demo",\n'
    '        version="0.1.0",\n'
    '        description="Prepared support inbox repo for Agent Graph demos.",\n'
    '        lifespan=lifespan,\n'
    '    )'
)
_APP_FACTORY_PATCHED_MIDDLEWARE = _APP_FACTORY_ANCHOR + (
    "\n"
    "    from .rate_limit import RateLimitMiddleware\n"
    "    app.add_middleware(RateLimitMiddleware)"
)


# ── Strategy dispatch ───────────────────────────────────────────────────────────

# Per-strategy marker written to rate_limit.py so we can distinguish later
# (e.g. for the eval badge or re-runs). Idempotency check is the file's
# existence — within a single worktree we only patch once.

DEFAULT_STRATEGY: StrategyHint = "route_local"


def _patch_route_local(worktree_path: str) -> bool:
    wt = Path(worktree_path)
    main_py = wt / "app" / "main.py"
    rate_limit_py = wt / "app" / "rate_limit.py"

    if not main_py.exists():
        return False
    if rate_limit_py.exists():
        return True

    source = main_py.read_text(encoding="utf-8")
    if _LOGIN_BODY_ANCHOR not in source:
        logger.warning("Mock runner [route_local]: anchor not found in %s", main_py)
        return False

    patched = source.replace(
        _LOGIN_BODY_ANCHOR,
        _LOGIN_RATE_LIMIT_GUARD_ROUTE_LOCAL + _LOGIN_BODY_ANCHOR,
        1,
    )
    main_py.write_text(patched, encoding="utf-8")
    rate_limit_py.write_text(_RATE_LIMIT_MODULE_ROUTE_LOCAL, encoding="utf-8")
    return True


def _patch_dependency(worktree_path: str) -> bool:
    wt = Path(worktree_path)
    main_py = wt / "app" / "main.py"
    rate_limit_py = wt / "app" / "rate_limit.py"

    if not main_py.exists():
        return False
    if rate_limit_py.exists():
        return True

    source = main_py.read_text(encoding="utf-8")
    if _LOGIN_SIGNATURE_ANCHOR not in source:
        logger.warning("Mock runner [dependency]: signature anchor not found in %s", main_py)
        return False

    # Add `Depends` import and our dependency import
    imports_block = "from fastapi import FastAPI, HTTPException, Query, Request"
    imports_block_patched = (
        "from fastapi import Depends, FastAPI, HTTPException, Query, Request\n"
        "\n"
        "from .rate_limit import enforce_login_rate_limit"
    )

    if imports_block in source:
        patched = source.replace(imports_block, imports_block_patched, 1)
    else:
        # Best-effort: prepend the import lines just below the first "from fastapi" line
        patched = source
        for line in source.splitlines():
            if line.startswith("from fastapi"):
                patched = source.replace(
                    line,
                    line + "\n\nfrom .rate_limit import enforce_login_rate_limit",
                    1,
                )
                if "Depends" not in line:
                    patched = patched.replace(
                        "from fastapi import",
                        "from fastapi import Depends,",
                        1,
                    )
                break

    patched = patched.replace(
        _LOGIN_SIGNATURE_ANCHOR,
        _LOGIN_SIGNATURE_PATCHED_DEPENDENCY,
        1,
    )

    main_py.write_text(patched, encoding="utf-8")
    rate_limit_py.write_text(_RATE_LIMIT_MODULE_DEPENDENCY, encoding="utf-8")
    return True


def _patch_middleware(worktree_path: str) -> bool:
    wt = Path(worktree_path)
    main_py = wt / "app" / "main.py"
    rate_limit_py = wt / "app" / "rate_limit.py"

    if not main_py.exists():
        return False
    if rate_limit_py.exists():
        return True

    source = main_py.read_text(encoding="utf-8")
    if _APP_FACTORY_ANCHOR not in source:
        logger.warning("Mock runner [middleware]: factory anchor not found in %s", main_py)
        return False

    patched = source.replace(_APP_FACTORY_ANCHOR, _APP_FACTORY_PATCHED_MIDDLEWARE, 1)
    main_py.write_text(patched, encoding="utf-8")
    rate_limit_py.write_text(_RATE_LIMIT_MODULE_MIDDLEWARE, encoding="utf-8")
    return True


_STRATEGIES: dict[StrategyHint, tuple[str, callable]] = {
    "route_local": ("route-local counter", _patch_route_local),
    "dependency": ("FastAPI dependency", _patch_dependency),
    "middleware": ("ASGI middleware", _patch_middleware),
}


def _apply_rate_limiting(worktree_path: str, strategy: StrategyHint | None = None) -> bool:
    """Patch app/main.py with rate limiting using the chosen strategy.

    Returns True on success or if already applied. Returns False when the
    worktree is not a PulseDesk-shaped repo (e.g. test fixtures).
    """
    chosen: StrategyHint = strategy if strategy in _STRATEGIES else DEFAULT_STRATEGY
    _label, patch_fn = _STRATEGIES[chosen]
    return patch_fn(worktree_path)


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


# ── Per-strategy log scripts ────────────────────────────────────────────────────

_LOG_SCRIPT: dict[StrategyHint, list[tuple[str, dict | None, float]]] = {
    "route_local": [
        ("text", {"content": "Reading the repository structure to understand the codebase..."}, 0.5),
        ("tool", {"tool_name": "Read", "tool_input": {"file_path": "app/main.py"}}, 0.4),
        ("tool", {"tool_name": "Read", "tool_input": {"file_path": "tests/test_rate_limit.py"}}, 0.4),
        ("text", {"content": "Strategy: route-local counter inside the login handler. Smallest diff, no middleware churn."}, 0.6),
        ("tool", {"tool_name": "Write", "tool_input": {"file_path": "app/rate_limit.py", "description": "in-memory per-IP counter"}}, 0.4),
        ("tool", {"tool_name": "Edit", "tool_input": {"file_path": "app/main.py", "description": "guard inserted at top of login handler"}}, 0.5),
        ("text", {"content": "Running the rate-limit acceptance tests..."}, 0.4),
        ("tool", {"tool_name": "Bash", "tool_input": {"command": "uv run pytest tests/test_rate_limit.py -v"}}, 1.0),
        ("tool", {"tool_name": "Bash", "tool_input": {"command": "git add -A && git commit -m 'agent: route-local rate limit'"}}, 0.3),
    ],
    "dependency": [
        ("text", {"content": "Reading the repository structure to understand the codebase..."}, 0.5),
        ("tool", {"tool_name": "Read", "tool_input": {"file_path": "app/main.py"}}, 0.4),
        ("tool", {"tool_name": "Read", "tool_input": {"file_path": "tests/test_rate_limit.py"}}, 0.4),
        ("text", {"content": "Strategy: FastAPI dependency via Depends(). Keeps the route body clean and the policy reusable."}, 0.6),
        ("tool", {"tool_name": "Write", "tool_input": {"file_path": "app/rate_limit.py", "description": "enforce_login_rate_limit dependency"}}, 0.4),
        ("tool", {"tool_name": "Edit", "tool_input": {"file_path": "app/main.py", "description": "Depends(enforce_login_rate_limit) added to login signature"}}, 0.5),
        ("text", {"content": "Running the rate-limit acceptance tests..."}, 0.4),
        ("tool", {"tool_name": "Bash", "tool_input": {"command": "uv run pytest tests/test_rate_limit.py -v"}}, 1.0),
        ("tool", {"tool_name": "Bash", "tool_input": {"command": "git add -A && git commit -m 'agent: dependency-based rate limit'"}}, 0.3),
    ],
    "middleware": [
        ("text", {"content": "Reading the repository structure to understand the codebase..."}, 0.5),
        ("tool", {"tool_name": "Read", "tool_input": {"file_path": "app/main.py"}}, 0.4),
        ("tool", {"tool_name": "Read", "tool_input": {"file_path": "tests/test_rate_limit.py"}}, 0.4),
        ("text", {"content": "Strategy: ASGI middleware. Centralised filter on POST /api/login, no per-route changes beyond registration."}, 0.6),
        ("tool", {"tool_name": "Write", "tool_input": {"file_path": "app/rate_limit.py", "description": "RateLimitMiddleware (Starlette BaseHTTPMiddleware)"}}, 0.4),
        ("tool", {"tool_name": "Edit", "tool_input": {"file_path": "app/main.py", "description": "app.add_middleware(RateLimitMiddleware) registered after factory"}}, 0.5),
        ("text", {"content": "Running the rate-limit acceptance tests..."}, 0.4),
        ("tool", {"tool_name": "Bash", "tool_input": {"command": "uv run pytest tests/test_rate_limit.py -v"}}, 1.0),
        ("tool", {"tool_name": "Bash", "tool_input": {"command": "git add -A && git commit -m 'agent: middleware-based rate limit'"}}, 0.3),
    ],
}


_COMPLETION_BLURB: dict[StrategyHint, str] = {
    "route_local": (
        "Implementation complete. Wrote app/rate_limit.py (in-memory per-IP counter) "
        "and inserted a 5-attempt / 60s guard at the top of POST /api/login. "
        "All 4 acceptance tests pass."
    ),
    "dependency": (
        "Implementation complete. Wrote app/rate_limit.py exposing enforce_login_rate_limit "
        "and added it to the login signature via Depends(). The handler body is unchanged. "
        "All 4 acceptance tests pass."
    ),
    "middleware": (
        "Implementation complete. Wrote app/rate_limit.py with RateLimitMiddleware and registered "
        "it on the FastAPI app. POST /api/login is filtered before the handler runs. "
        "All 4 acceptance tests pass."
    ),
}


class MockAgentRunner(AgentRunner):
    """Simulates an agent run without calling the LLM API.

    Used when AGENT_GRAPH_ENABLE_REAL_RUNS=false (the default). Each strategy
    writes a real, test-passing rate-limit implementation so the diff and
    merge flows work end-to-end during demos with no external dependencies.
    """

    async def stream(
        self,
        node_id: str,
        prompt: str,
        worktree_path: str,
        strategy: StrategyHint | None = None,
    ) -> AsyncGenerator[NormalizedEvent, None]:
        wt = Path(worktree_path)
        chosen: StrategyHint = strategy if strategy in _STRATEGIES else DEFAULT_STRATEGY
        script = _LOG_SCRIPT[chosen]

        yield NormalizedEvent(type="agent_started", node_id=node_id)
        await asyncio.sleep(0.3)

        success = _apply_rate_limiting(worktree_path, strategy=chosen)

        if not success:
            # Worktree is not a PulseDesk repo; write a placeholder so the
            # diff/merge surface still demonstrates wiring end-to-end.
            placeholder = wt / "agent_notes.md"
            yield NormalizedEvent(
                type="agent_tool_use",
                node_id=node_id,
                tool_name="Write",
                tool_input={"file_path": "agent_notes.md", "description": f"placeholder ({chosen})"},
            )
            placeholder.write_text(
                f"# Mock Agent Notes\n\nStrategy: {chosen}\n"
                "This worktree does not contain a PulseDesk app; nothing to patch.\n"
            )
            _git_commit(worktree_path, f"agent[{chosen}]: placeholder notes")
            yield NormalizedEvent(
                type="agent_completed",
                node_id=node_id,
                content=f"Mock run complete (strategy={chosen}, placeholder; not a PulseDesk repo).",
            )
            return

        for kind, payload, sleep_for in script:
            if kind == "text":
                yield NormalizedEvent(
                    type="agent_text",
                    node_id=node_id,
                    content=payload["content"],
                )
            elif kind == "tool":
                yield NormalizedEvent(
                    type="agent_tool_use",
                    node_id=node_id,
                    tool_name=payload["tool_name"],
                    tool_input=payload.get("tool_input", {}),
                )
            await asyncio.sleep(sleep_for)

        _git_commit(worktree_path, f"agent[{chosen}]: rate limit on POST /api/login")

        yield NormalizedEvent(
            type="agent_completed",
            node_id=node_id,
            content=_COMPLETION_BLURB[chosen],
        )
