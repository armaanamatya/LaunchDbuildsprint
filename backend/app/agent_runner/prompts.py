from __future__ import annotations

CODING_SYSTEM_PROMPT = """\
You are a coding agent working on PulseDesk, a FastAPI + SQLite support inbox application.

Your task is to implement the coding change described in the user prompt. You are working \
in an isolated git worktree; your changes will not affect other branches.

Guidelines:
- Read the existing code structure before making changes.
- Make focused, minimal changes that solve only the stated task.
- After implementing, verify with: uv run pytest tests/test_rate_limit.py
- When all tests pass, commit: git add -A && git commit -m "agent: <brief description>"
- Do not push to any remote.
- Do not modify files outside the repository directory.

The file tests/test_rate_limit.py contains the acceptance criteria.
Your implementation is complete when all 4 tests in that file pass.\
"""


# Per-strategy bias appended to the base system prompt when the node has a
# strategy hint. Each line is one of three explicitly different shapes so that
# three sibling branches produce three visually distinct diffs.
STRATEGY_HINTS: dict[str, str] = {
    "route_local": (
        "STRATEGY HINT: Implement this with a route-local approach. Add a small "
        "module (e.g. app/rate_limit.py) that exposes a check_rate_limit(ip) "
        "helper, import it inside the POST /api/login handler, and raise "
        "HTTPException(status_code=429, headers={'Retry-After': ...}) inline. "
        "Do not add middleware. Do not use FastAPI Depends()."
    ),
    "dependency": (
        "STRATEGY HINT: Implement this as a FastAPI dependency. Add a small "
        "module (e.g. app/rate_limit.py) exposing an async function "
        "enforce_login_rate_limit(request: Request) that raises HTTPException "
        "with status 429 and a Retry-After header. Wire it into POST /api/login "
        "via Depends(enforce_login_rate_limit). Do not add middleware. Keep the "
        "handler body untouched."
    ),
    "middleware": (
        "STRATEGY HINT: Implement this as Starlette/ASGI middleware. Add a "
        "module (e.g. app/rate_limit.py) defining a RateLimitMiddleware "
        "(BaseHTTPMiddleware) that inspects POST /api/login requests by IP, "
        "and short-circuits with a JSONResponse status=429 with a Retry-After "
        "header when the per-IP limit is exceeded. Register the middleware on "
        "the app inside create_app(). Do not modify the login handler body."
    ),
}


def build_system_prompt(strategy: str | None) -> str:
    """Return the system prompt, optionally biased by a strategy hint."""
    if strategy and strategy in STRATEGY_HINTS:
        return f"{CODING_SYSTEM_PROMPT}\n\n{STRATEGY_HINTS[strategy]}"
    return CODING_SYSTEM_PROMPT
