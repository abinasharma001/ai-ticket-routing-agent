import sqlite3
import json
import os
from loguru import logger
from typing import List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "tickets.db")
SEED_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "seed_tickets.json")

def init_db():
    """Initialize the SQLite database and populate with seed data if empty."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
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
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            input_text TEXT,
            category TEXT,
            department TEXT,
            confidence REAL
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM tickets")
    count = cursor.fetchone()[0]
    
    if count == 0:
        logger.info("Database is empty. Loading seed data...")
        if os.path.exists(SEED_DATA_PATH):
            with open(SEED_DATA_PATH, "r", encoding="utf-8") as f:
                seed_data = json.load(f)
                
            for item in seed_data:
                cursor.execute("""
                    INSERT INTO tickets (id, subject, description, category, department, resolution, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get("id"),
                    item.get("subject"),
                    item.get("description"),
                    item.get("category"),
                    item.get("department"),
                    item.get("resolution"),
                    item.get("created_at"),
                    item.get("updated_at"),
                    json.dumps(item.get("metadata", {}))
                ))
            conn.commit()
            logger.info(f"Loaded {len(seed_data)} tickets from seed data.")
        else:
            logger.warning(f"Seed data not found at {SEED_DATA_PATH}")
            
    conn.close()

def get_all_tickets() -> List[Dict[str, Any]]:
    """Retrieve all tickets from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tickets")
    rows = cursor.fetchall()
    conn.close()
    
    tickets = []
    for row in rows:
        ticket = dict(row)
        if ticket.get("metadata"):
            try:
                ticket["metadata"] = json.loads(ticket["metadata"])
            except json.JSONDecodeError:
                ticket["metadata"] = {}
        tickets.append(ticket)
        
    return tickets

def log_prediction(input_text: str, category: str, department: str, confidence: float):
    """Log a prediction to the history table."""
    from datetime import datetime
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO prediction_history (timestamp, input_text, category, department, confidence)
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(),
        input_text,
        category,
        department,
        confidence
    ))
    conn.commit()
    conn.close()

def get_prediction_history() -> List[Dict[str, Any]]:
    """Retrieve all prediction history."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM prediction_history ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]
