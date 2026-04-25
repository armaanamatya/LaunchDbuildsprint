from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.worktree_service import sanitize_branch_segment, worktree_service


client = TestClient(app)


def test_repo_endpoint_exposes_demo_repo_config() -> None:
    response = client.get("/api/v1/repo")

    assert response.status_code == 200
    payload = response.json()
    assert payload["repo_path"] is not None
    assert payload["repo_path"].endswith("demo-repo")
    assert payload["repo_exists"] is True
    assert payload["base_branch"] == "main"


def test_worktree_plan_endpoint_uses_parent_branch_shape() -> None:
    create_response = client.post(
        "/api/v1/nodes",
        json={"label": "Rate limit login", "parent_id": "root", "prompt": "Add a rate limiter."},
    )
    assert create_response.status_code == 200
    node_id = create_response.json()["id"]

    plan_response = client.get(f"/api/v1/nodes/{node_id}/worktree-plan")

    assert plan_response.status_code == 200
    payload = plan_response.json()
    assert payload["node_id"] == node_id
    assert payload["branch_name"].startswith("agent/")
    assert payload["worktree_path"].endswith(payload["branch_name"].replace("/", "-"))
    assert payload["implemented"] is False


def test_branch_name_and_worktree_path_are_sanitized() -> None:
    assert sanitize_branch_segment("Feature Branch #1") == "feature-branch-1"

    branch_name = worktree_service.build_branch_name("Main Branch", "node:42")
    worktree_path = Path(worktree_service.build_worktree_path(branch_name))

    assert branch_name == "agent/node-42"
    assert worktree_path.name == "agent-node-42"
