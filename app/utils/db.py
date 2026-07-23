from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator, List

from loguru import logger

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "tickets.db")
SEED_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "seed_tickets.json")


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def _ensure_indexes(connection: sqlite3.Connection) -> None:
    connection.execute("CREATE INDEX IF NOT EXISTS idx_prediction_history_timestamp ON prediction_history(timestamp DESC)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_tickets_department ON tickets(department)")


def _ensure_prediction_history_schema(connection: sqlite3.Connection) -> None:
    columns = {row[1] for row in connection.execute("PRAGMA table_info(prediction_history)")}
    if "processing_ms" not in columns:
        connection.execute("ALTER TABLE prediction_history ADD COLUMN processing_ms REAL")

def init_db():
    """Initialize the SQLite database and populate with seed data if empty."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    try:
        with _connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY,
                    subject TEXT,
                    description TEXT,
                    category TEXT,
                    department TEXT,
                    resolution TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    metadata TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS prediction_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    input_text TEXT,
                    category TEXT,
                    department TEXT,
                    confidence REAL,
                    processing_ms REAL
                )
                """
            )
            _ensure_prediction_history_schema(connection)
            _ensure_indexes(connection)

            cursor = connection.execute("SELECT COUNT(*) FROM tickets")
            count = cursor.fetchone()[0]

            if count == 0:
                logger.info("Database is empty. Loading seed data...")
                if os.path.exists(SEED_DATA_PATH):
                    with open(SEED_DATA_PATH, "r", encoding="utf-8") as file_handle:
                        seed_data = json.load(file_handle)

                    for item in seed_data:
                        connection.execute(
                            """
                            INSERT OR IGNORE INTO tickets (
                                id, subject, description, category, department, resolution,
                                created_at, updated_at, metadata
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                item.get("id"),
                                item.get("subject"),
                                item.get("description"),
                                item.get("category"),
                                item.get("department"),
                                item.get("resolution"),
                                item.get("created_at"),
                                item.get("updated_at"),
                                json.dumps(item.get("metadata", {}), ensure_ascii=False),
                            ),
                        )
                    logger.info("Loaded %s tickets from seed data.", len(seed_data))
                else:
                    logger.warning("Seed data not found at %s", SEED_DATA_PATH)

            connection.commit()
    except sqlite3.DatabaseError as exc:
        logger.exception("Failed to initialize SQLite database: %s", exc)

def get_all_tickets() -> List[Dict[str, Any]]:
    """Retrieve all tickets from the database."""
    try:
        with _connect() as connection:
            rows = connection.execute("SELECT * FROM tickets ORDER BY id ASC").fetchall()

        tickets: list[dict[str, Any]] = []
        for row in rows:
            ticket = dict(row)
            if ticket.get("metadata"):
                try:
                    ticket["metadata"] = json.loads(ticket["metadata"])
                except json.JSONDecodeError:
                    ticket["metadata"] = {}
            tickets.append(ticket)

        return tickets
    except sqlite3.DatabaseError as exc:
        logger.exception("Failed to load tickets: %s", exc)
        return []

def log_prediction(
    input_text: str,
    category: str,
    department: str,
    confidence: float,
    processing_ms: float | None = None,
) -> None:
    """Log a prediction to the history table."""
    try:
        with _connect() as connection:
            connection.execute(
                """
                INSERT INTO prediction_history (
                    timestamp, input_text, category, department, confidence, processing_ms
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(timespec="seconds") + "Z",
                    input_text,
                    category,
                    department,
                    confidence,
                    processing_ms,
                ),
            )
            connection.commit()
    except sqlite3.DatabaseError as exc:
        logger.exception("Failed to write prediction history: %s", exc)

def get_prediction_history() -> List[Dict[str, Any]]:
    """Retrieve all prediction history."""
    try:
        with _connect() as connection:
            rows = connection.execute("SELECT * FROM prediction_history ORDER BY id DESC").fetchall()

        return [dict(row) for row in rows]
    except sqlite3.DatabaseError as exc:
        logger.exception("Failed to read prediction history: %s", exc)
        return []
