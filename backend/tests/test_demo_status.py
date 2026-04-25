"""
Tests for ``GET /api/v1/demo/status`` — the one-call demo readiness probe.

Per critique #3: ``ready=True`` requires not just that the prerequisites
*could* be satisfied, but that the backend is in a fresh, ready-to-run
state — no running tasks, no leaked worktrees.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import httpx
import pytest

from app.main import app
from app.settings import get_settings


pytestmark = pytest.mark.anyio


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    )


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )


# ── happy / not-ready paths ────────────────────────────────────────────────────


async def test_status_ready_on_fresh_isolated_backend(isolated_backend: Path) -> None:
    async with _client() as client:
        response = await client.get("/api/v1/demo/status")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ready"] is True, f"expected ready=True, issues={payload['issues']}"
    assert payload["demo_repo_exists"] is True
    assert payload["demo_repo_is_git"] is True
    assert payload["base_branch_clean"] is True
    assert payload["active_worktrees"] == 0
    assert payload["running_tasks"] == 0
    assert payload["enable_real_runs"] is False
    assert payload["anthropic_api_key_present"] is False
    assert payload["issues"] == []


async def test_status_not_ready_when_worktrees_exist(isolated_backend: Path) -> None:
    """active_worktrees > 0 must take ready to False (critique #3)."""
    async with _client() as client:
        triple = await client.post(
            "/api/v1/branches/triple",
            json={"parent_id": "root", "prompt": "x", "auto_run": False},
        )
        assert triple.status_code == 200

        status = await client.get("/api/v1/demo/status")

    payload = status.json()
    assert payload["ready"] is False
    assert payload["active_worktrees"] == 3
    assert any("worktree(s) still on disk" in issue for issue in payload["issues"])


async def test_status_not_ready_when_working_tree_dirty(isolated_backend: Path) -> None:
    (isolated_backend / "uncommitted.txt").write_text("dirty\n")

    async with _client() as client:
        response = await client.get("/api/v1/demo/status")

    payload = response.json()
    assert payload["ready"] is False
    assert payload["base_branch_clean"] is False
    assert any("dirty" in issue.lower() for issue in payload["issues"])


async def test_status_not_ready_when_real_runs_enabled_without_key(
    isolated_backend: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AGENT_GRAPH_ENABLE_REAL_RUNS", "true")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    get_settings.cache_clear()

    async with _client() as client:
        response = await client.get("/api/v1/demo/status")

    payload = response.json()
    assert payload["ready"] is False
    assert payload["enable_real_runs"] is True
    assert payload["anthropic_api_key_present"] is False
    assert any("ANTHROPIC_API_KEY" in issue for issue in payload["issues"])


async def test_status_not_ready_when_eval_enabled_without_uv(
    isolated_backend: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AGENT_GRAPH_ENABLE_EVAL", "true")
    monkeypatch.setattr("app.api.shutil.which", lambda _name: None)
    get_settings.cache_clear()

    async with _client() as client:
        response = await client.get("/api/v1/demo/status")

    payload = response.json()
    assert payload["enable_eval"] is True
    assert payload["uv_on_path"] is False
    assert payload["ready"] is False
    assert any("uv" in issue.lower() for issue in payload["issues"])


async def test_status_ready_when_real_runs_enabled_with_key(
    isolated_backend: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AGENT_GRAPH_ENABLE_REAL_RUNS", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-not-used")
    get_settings.cache_clear()

    async with _client() as client:
        response = await client.get("/api/v1/demo/status")

    payload = response.json()
    assert payload["enable_real_runs"] is True
    assert payload["anthropic_api_key_present"] is True
    # Boolean correctness: presence is reported as True; the value itself
    # must NEVER appear in the response payload (P2-D contract).
    assert "sk-test-fake-not-used" not in response.text
    assert payload["ready"] is True


async def test_status_never_leaks_anthropic_api_key_value(
    isolated_backend: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = "sk-this-must-never-appear-in-any-response"
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret)
    get_settings.cache_clear()

    async with _client() as client:
        response = await client.get("/api/v1/demo/status")

    assert secret not in response.text
