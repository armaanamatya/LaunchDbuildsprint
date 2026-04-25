from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .security import hash_password

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "support_inbox.db"

SCHEMA_SQL = """
CREATE TABLE agents (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    team TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE tickets (
    id INTEGER PRIMARY KEY,
    external_id TEXT NOT NULL UNIQUE,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    subject TEXT NOT NULL,
    status TEXT NOT NULL,
    priority TEXT NOT NULL,
    queue TEXT NOT NULL,
    summary TEXT NOT NULL,
    assigned_agent_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_message_at TEXT NOT NULL,
    FOREIGN KEY (assigned_agent_id) REFERENCES agents (id)
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    ticket_id INTEGER NOT NULL,
    author_name TEXT NOT NULL,
    author_role TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES tickets (id) ON DELETE CASCADE
);
"""

AGENTS = [
    (1, "alex@pulsedesk.test", "Alex Morgan", "Support Lead", "Core Inbox", hash_password("demo123"), 1),
    (2, "priya@pulsedesk.test", "Priya Shah", "Support Engineer", "Billing", hash_password("demo123"), 1),
    (3, "jordan@pulsedesk.test", "Jordan Lee", "Support Engineer", "Platform", hash_password("demo123"), 1),
    (4, "sam@pulsedesk.test", "Sam Rivera", "Contractor", "Overflow", hash_password("demo123"), 0),
]

TICKETS = [
    (
        1,
        "PD-1042",
        "Harper Sloan",
        "harper@northstar.app",
        "Refund failed for annual upgrade",
        "open",
        "high",
        "billing",
        "Customer upgraded to annual but the refund for the previous monthly plan did not process.",
        2,
        "2026-04-22T09:14:00Z",
        "2026-04-24T14:03:00Z",
        "2026-04-24T14:03:00Z",
    ),
    (
        2,
        "PD-1041",
        "Milo Chen",
        "milo@driftlane.io",
        "Cannot export team activity CSV",
        "pending_customer",
        "medium",
        "platform",
        "Export spinner never finishes for large workspace audit logs.",
        3,
        "2026-04-21T16:48:00Z",
        "2026-04-24T11:27:00Z",
        "2026-04-24T11:27:00Z",
    ),
    (
        3,
        "PD-1039",
        "Avery Brooks",
        "avery@luminhq.dev",
        "Magic link expires instantly",
        "open",
        "urgent",
        "authentication",
        "New users report that emailed magic links are already expired on first click.",
        1,
        "2026-04-20T08:30:00Z",
        "2026-04-24T08:01:00Z",
        "2026-04-24T08:01:00Z",
    ),
    (
        4,
        "PD-1038",
        "Noah Patel",
        "noah@fablelab.com",
        "Webhook retries are delayed",
        "resolved",
        "low",
        "platform",
        "Webhook delivery retry cadence looks much slower than documented.",
        3,
        "2026-04-18T13:12:00Z",
        "2026-04-23T17:44:00Z",
        "2026-04-23T17:44:00Z",
    ),
    (
        5,
        "PD-1037",
        "Emma Costa",
        "emma@brightpath.co",
        "Mobile nav overlaps composer",
        "open",
        "medium",
        "product",
        "Support agents on smaller laptops cannot see the full reply composer when the nav is pinned.",
        1,
        "2026-04-17T10:05:00Z",
        "2026-04-24T09:40:00Z",
        "2026-04-24T09:40:00Z",
    ),
    (
        6,
        "PD-1034",
        "Owen Diaz",
        "owen@eagleview.ai",
        "Seat count changed after SSO rollout",
        "pending_internal",
        "high",
        "billing",
        "Workspace shows 24 billable seats after SCIM import even though only 19 members are active.",
        2,
        "2026-04-16T11:22:00Z",
        "2026-04-23T15:18:00Z",
        "2026-04-23T15:18:00Z",
    ),
]

MESSAGES = [
    (
        1,
        1,
        "Harper Sloan",
        "customer",
        "I upgraded to annual this morning and still see the monthly charge in my bank feed.",
        "2026-04-22T09:14:00Z",
    ),
    (
        2,
        1,
        "Priya Shah",
        "agent",
        "I can confirm the upgrade completed. I'm checking why the monthly refund did not enqueue.",
        "2026-04-24T14:03:00Z",
    ),
    (
        3,
        2,
        "Milo Chen",
        "customer",
        "The CSV export has been spinning for 15 minutes on two browsers.",
        "2026-04-21T16:48:00Z",
    ),
    (
        4,
        2,
        "Jordan Lee",
        "agent",
        "Could you share roughly how many users are in the workspace and whether filters are applied?",
        "2026-04-24T11:27:00Z",
    ),
    (
        5,
        3,
        "Avery Brooks",
        "customer",
        "Every magic link says expired before I can even paste it into the browser.",
        "2026-04-20T08:30:00Z",
    ),
    (
        6,
        3,
        "Alex Morgan",
        "agent",
        "Thanks, we are investigating token timestamps and session clocks on the auth service.",
        "2026-04-24T08:01:00Z",
    ),
    (
        7,
        4,
        "Noah Patel",
        "customer",
        "Our webhook retries came through hours later than expected.",
        "2026-04-18T13:12:00Z",
    ),
    (
        8,
        4,
        "Jordan Lee",
        "agent",
        "We found an old backoff setting in your workspace shard and corrected it.",
        "2026-04-23T17:44:00Z",
    ),
    (
        9,
        5,
        "Emma Costa",
        "customer",
        "The sidebar sits over the reply box when I open a ticket on my 13-inch screen.",
        "2026-04-17T10:05:00Z",
    ),
    (
        10,
        5,
        "Alex Morgan",
        "agent",
        "I reproduced this in Chrome at 1280px width and filed it with the product team.",
        "2026-04-24T09:40:00Z",
    ),
    (
        11,
        6,
        "Owen Diaz",
        "customer",
        "Billing jumped after we rolled out SCIM. I think disabled accounts are still counted.",
        "2026-04-16T11:22:00Z",
    ),
    (
        12,
        6,
        "Priya Shah",
        "agent",
        "Engineering is checking how SCIM deactivations map into billable seat reconciliation.",
        "2026-04-23T15:18:00Z",
    ),
]


def resolve_db_path(explicit_path: Path | str | None = None) -> Path:
    if explicit_path is not None:
        return Path(explicit_path)

    configured = os.getenv("SUPPORT_INBOX_DB_PATH")
    if configured:
        return Path(configured)

    return DEFAULT_DB_PATH


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = resolve_db_path(db_path)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def open_connection(db_path: Path | str | None = None):
    connection = connect(db_path)
    try:
        yield connection
    finally:
        connection.close()


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA_SQL)


def seed_database(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT INTO agents (id, email, full_name, role, team, password_hash, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        AGENTS,
    )
    connection.executemany(
        """
        INSERT INTO tickets (
            id,
            external_id,
            customer_name,
            customer_email,
            subject,
            status,
            priority,
            queue,
            summary,
            assigned_agent_id,
            created_at,
            updated_at,
            last_message_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        TICKETS,
    )
    connection.executemany(
        """
        INSERT INTO messages (id, ticket_id, author_name, author_role, body, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        MESSAGES,
    )


def ensure_database(db_path: Path | str | None = None) -> Path:
    path = resolve_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        reset_database(path)
    return path


def reset_database(db_path: Path | str | None = None) -> Path:
    path = resolve_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    with open_connection(path) as connection:
        create_schema(connection)
        seed_database(connection)
        connection.commit()

    return path
