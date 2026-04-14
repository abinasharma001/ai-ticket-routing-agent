from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ticket_router_agent.domain.models import TicketCategory, TicketRecord


@dataclass
class SQLiteTicketRepository:
    database_path: Path

    def __post_init__(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    department TEXT NOT NULL,
                    resolution TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    actual_category TEXT NOT NULL,
                    actual_department TEXT NOT NULL,
                    was_helpful INTEGER,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def upsert_ticket(self, ticket: TicketRecord) -> TicketRecord:
        with self._connect() as connection:
            if ticket.id is None:
                cursor = connection.execute(
                    """
                    INSERT INTO tickets (subject, description, category, department, resolution, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ticket.subject,
                        ticket.description,
                        ticket.category.value,
                        ticket.department,
                        ticket.resolution,
                        ticket.created_at.isoformat(),
                        ticket.updated_at.isoformat(),
                        json.dumps(ticket.metadata),
                    ),
                )
                ticket.id = int(cursor.lastrowid)
            else:
                connection.execute(
                    """
                    UPDATE tickets
                    SET subject = ?, description = ?, category = ?, department = ?, resolution = ?, updated_at = ?, metadata = ?
                    WHERE id = ?
                    """,
                    (
                        ticket.subject,
                        ticket.description,
                        ticket.category.value,
                        ticket.department,
                        ticket.resolution,
                        datetime.utcnow().isoformat(),
                        json.dumps(ticket.metadata),
                        ticket.id,
                    ),
                )
            connection.commit()
        return ticket

    def list_tickets(self) -> list[TicketRecord]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM tickets ORDER BY id ASC").fetchall()
        return [self._row_to_ticket(row) for row in rows]

    def get_ticket(self, ticket_id: int) -> TicketRecord | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_ticket(row)

    def record_feedback(self, payload: dict) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO feedback (ticket_id, actual_category, actual_department, was_helpful, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["ticket_id"],
                    payload["actual_category"],
                    payload["actual_department"],
                    payload.get("was_helpful"),
                    payload.get("notes"),
                    datetime.utcnow().isoformat(),
                ),
            )
            connection.commit()

    def _row_to_ticket(self, row: sqlite3.Row) -> TicketRecord:
        return TicketRecord(
            id=row["id"],
            subject=row["subject"],
            description=row["description"],
            category=TicketCategory(row["category"]),
            department=row["department"],
            resolution=row["resolution"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            metadata=json.loads(row["metadata"]),
        )
