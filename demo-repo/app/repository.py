from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from sqlite3 import Row

from .db import open_connection


def _ticket_select_sql() -> str:
    return """
        SELECT
            t.id,
            t.external_id,
            t.customer_name,
            t.customer_email,
            t.subject,
            t.status,
            t.priority,
            t.queue,
            t.summary,
            a.full_name AS assigned_agent,
            t.created_at,
            t.updated_at,
            t.last_message_at,
            COUNT(m.id) AS message_count
        FROM tickets t
        LEFT JOIN agents a ON a.id = t.assigned_agent_id
        LEFT JOIN messages m ON m.ticket_id = t.id
    """


def _serialize_ticket(row: Row) -> dict[str, object]:
    return {
        "id": row["id"],
        "external_id": row["external_id"],
        "customer_name": row["customer_name"],
        "customer_email": row["customer_email"],
        "subject": row["subject"],
        "status": row["status"],
        "priority": row["priority"],
        "queue": row["queue"],
        "summary": row["summary"],
        "assigned_agent": row["assigned_agent"],
        "message_count": row["message_count"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "last_message_at": row["last_message_at"],
    }


def get_agent_by_email(db_path: Path, email: str) -> dict[str, object] | None:
    with open_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, email, full_name, role, team, password_hash, is_active
            FROM agents
            WHERE lower(email) = lower(?)
            """,
            (email.strip(),),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def list_tickets(db_path: Path, query: str = "", status: str | None = None, limit: int = 25) -> list[dict[str, object]]:
    normalized_query = query.strip().lower()
    normalized_status = status.strip().lower() if status else None
    safe_limit = max(1, min(limit, 50))
    where_clauses: list[str] = []
    params: list[object] = []

    if normalized_query:
        where_clauses.append(
            """
            (
                lower(t.external_id) LIKE ?
                OR lower(t.customer_name) LIKE ?
                OR lower(t.customer_email) LIKE ?
                OR lower(t.subject) LIKE ?
                OR lower(t.summary) LIKE ?
            )
            """
        )
        wildcard = f"%{normalized_query}%"
        params.extend([wildcard, wildcard, wildcard, wildcard, wildcard])

    if normalized_status:
        where_clauses.append("lower(t.status) = ?")
        params.append(normalized_status)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    sql = f"""
        {_ticket_select_sql()}
        {where_sql}
        GROUP BY
            t.id,
            t.external_id,
            t.customer_name,
            t.customer_email,
            t.subject,
            t.status,
            t.priority,
            t.queue,
            t.summary,
            a.full_name,
            t.created_at,
            t.updated_at,
            t.last_message_at
        ORDER BY t.last_message_at DESC
        LIMIT ?
    """
    params.append(safe_limit)

    with open_connection(db_path) as connection:
        rows = connection.execute(sql, params).fetchall()

    return [_serialize_ticket(row) for row in rows]


def get_ticket_detail(db_path: Path, ticket_id: int) -> dict[str, object] | None:
    with open_connection(db_path) as connection:
        ticket_row = connection.execute(
            f"""
            {_ticket_select_sql()}
            WHERE t.id = ?
            GROUP BY
                t.id,
                t.external_id,
                t.customer_name,
                t.customer_email,
                t.subject,
                t.status,
                t.priority,
                t.queue,
                t.summary,
                a.full_name,
                t.created_at,
                t.updated_at,
                t.last_message_at
            """,
            (ticket_id,),
        ).fetchone()
        if ticket_row is None:
            return None

        message_rows = connection.execute(
            """
            SELECT id, author_name, author_role, body, created_at
            FROM messages
            WHERE ticket_id = ?
            ORDER BY created_at ASC
            """,
            (ticket_id,),
        ).fetchall()

    ticket = _serialize_ticket(ticket_row)
    ticket["messages"] = [dict(row) for row in message_rows]
    return ticket


def get_dashboard_data(db_path: Path) -> dict[str, object]:
    with open_connection(db_path) as connection:
        counts = connection.execute(
            """
            SELECT
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) AS open_tickets,
                SUM(CASE WHEN status = 'pending_customer' THEN 1 ELSE 0 END) AS waiting_on_customer,
                SUM(CASE WHEN priority IN ('high', 'urgent') THEN 1 ELSE 0 END) AS high_priority,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved_tickets
            FROM tickets
            """
        ).fetchone()

    recent_tickets = list_tickets(db_path=db_path, limit=4)
    return {
        "stats": {
            "open_tickets": counts["open_tickets"] or 0,
            "waiting_on_customer": counts["waiting_on_customer"] or 0,
            "high_priority": counts["high_priority"] or 0,
            "resolved_tickets": counts["resolved_tickets"] or 0,
        },
        "recent_tickets": recent_tickets,
    }


def add_ticket_reply(db_path: Path, ticket_id: int, author_name: str, body: str, status: str) -> dict[str, object] | None:
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    with open_connection(db_path) as connection:
        existing = connection.execute("SELECT id FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if existing is None:
            return None

        connection.execute(
            """
            INSERT INTO messages (ticket_id, author_name, author_role, body, created_at)
            VALUES (?, ?, 'agent', ?, ?)
            """,
            (ticket_id, author_name.strip(), body.strip(), timestamp),
        )
        connection.execute(
            """
            UPDATE tickets
            SET status = ?, updated_at = ?, last_message_at = ?
            WHERE id = ?
            """,
            (status.strip().lower(), timestamp, timestamp, ticket_id),
        )
        connection.commit()

    return get_ticket_detail(db_path, ticket_id)
