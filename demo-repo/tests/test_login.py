from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.db import reset_database
from app.main import create_app


def test_login_returns_access_token_for_seeded_agent(client: TestClient) -> None:
    response = client.post(
        "/api/login",
        json={"email": "alex@pulsedesk.test", "password": "demo123"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "demo-1-alex",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "email": "alex@pulsedesk.test",
            "full_name": "Alex Morgan",
            "role": "Support Lead",
            "team": "Core Inbox",
        },
    }


def test_login_rejects_invalid_password(client: TestClient) -> None:
    response = client.post(
        "/api/login",
        json={"email": "alex@pulsedesk.test", "password": "wrong-pass"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_login_rejects_inactive_user(client: TestClient) -> None:
    response = client.post(
        "/api/login",
        json={"email": "sam@pulsedesk.test", "password": "demo123"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Account is inactive"}


def test_seeded_ticket_search_returns_known_results(client: TestClient) -> None:
    response = client.get("/api/tickets", params={"q": "refund"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["external_id"] == "PD-1042"


def test_reset_database_restores_known_baseline(tmp_path: Path) -> None:
    db_path = tmp_path / "reset_flow.db"
    reset_database(db_path)

    app = create_app(db_path=db_path)
    with TestClient(app) as client:
        before = client.get("/api/tickets/1")
        assert before.status_code == 200
        before_payload = before.json()

        dirty = client.post(
            "/api/tickets/1/reply",
            json={
                "author_name": "Alex Morgan",
                "body": "We manually retriggered the refund workflow and are monitoring the ledger.",
                "status": "pending_customer",
            },
        )
        assert dirty.status_code == 200
        assert len(dirty.json()["ticket"]["messages"]) == len(before_payload["messages"]) + 1

    reset_database(db_path)

    clean_app = create_app(db_path=db_path)
    with TestClient(clean_app) as clean_client:
        after = clean_client.get("/api/tickets/1")
        assert after.status_code == 200
        after_payload = after.json()

    assert len(after_payload["messages"]) == len(before_payload["messages"])
    assert after_payload["updated_at"] == before_payload["updated_at"]
