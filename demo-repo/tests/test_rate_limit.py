"""
Hero task: add rate limiting to POST /api/login.

These tests define the acceptance criteria for the hero task.
They currently FAIL because rate limiting is not implemented.

Agent branches will each implement rate limiting and need to make these pass.
The implementation strategy is intentionally left open:
  - Branch A might use a route-local counter
  - Branch B might use a decorator/dependency
  - Branch C might use slowapi middleware

Expected behavior:
  - Allow up to RATE_LIMIT_MAX_ATTEMPTS login attempts per IP within RATE_LIMIT_WINDOW_SECONDS
  - Return HTTP 429 when the limit is exceeded
  - Include a Retry-After header in the 429 response
  - Successful logins count toward the limit to prevent enumeration
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW_SECONDS = 60


def test_login_allows_attempts_under_the_limit(client: TestClient) -> None:
    """Requests under the threshold must not be blocked."""
    for i in range(RATE_LIMIT_MAX_ATTEMPTS - 1):
        response = client.post(
            "/api/login",
            json={"email": f"user{i}@nowhere.test", "password": "wrong"},
        )
        assert response.status_code != 429, (
            f"Request {i + 1} was rate-limited before the threshold was reached"
        )


def test_login_returns_429_after_limit_exceeded(client: TestClient) -> None:
    """The request that exceeds the limit must return 429."""
    for _ in range(RATE_LIMIT_MAX_ATTEMPTS):
        client.post(
            "/api/login",
            json={"email": "attacker@nowhere.test", "password": "wrong"},
        )

    response = client.post(
        "/api/login",
        json={"email": "attacker@nowhere.test", "password": "wrong"},
    )
    assert response.status_code == 429, (
        f"Expected 429 after {RATE_LIMIT_MAX_ATTEMPTS} attempts, got {response.status_code}"
    )


def test_rate_limit_response_includes_retry_after_header(client: TestClient) -> None:
    """The 429 response must include a Retry-After header so callers know when to retry."""
    for _ in range(RATE_LIMIT_MAX_ATTEMPTS):
        client.post(
            "/api/login",
            json={"email": "attacker@nowhere.test", "password": "wrong"},
        )

    response = client.post(
        "/api/login",
        json={"email": "attacker@nowhere.test", "password": "wrong"},
    )
    assert response.status_code == 429
    assert "retry-after" in response.headers, (
        "429 response must include a Retry-After header"
    )


def test_successful_login_counts_toward_rate_limit(client: TestClient) -> None:
    """Successful logins count toward the limit to prevent credential enumeration."""
    for _ in range(RATE_LIMIT_MAX_ATTEMPTS):
        client.post(
            "/api/login",
            json={"email": "alex@pulsedesk.test", "password": "demo123"},
        )

    response = client.post(
        "/api/login",
        json={"email": "alex@pulsedesk.test", "password": "demo123"},
    )
    assert response.status_code == 429, (
        "Successful logins should also count toward the rate limit"
    )


def test_rate_limit_applies_regardless_of_email(client: TestClient) -> None:
    """The rate limit is per-IP, not per-email, so rotating emails does not bypass it."""
    for i in range(RATE_LIMIT_MAX_ATTEMPTS):
        client.post(
            "/api/login",
            json={"email": f"variant{i}@nowhere.test", "password": "wrong"},
        )

    response = client.post(
        "/api/login",
        json={"email": "different@nowhere.test", "password": "wrong"},
    )
    assert response.status_code == 429, (
        "Rotating the email address must not bypass the rate limit"
    )
