import json
import os
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).parent / "data" / "openops.sqlite3"

class Storage:
    def __init__(self, db_path=None):
        self.db_path = str(db_path or os.getenv("OPENOPS_DB_PATH") or DEFAULT_DB)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS finance_records (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id TEXT NOT NULL UNIQUE,
                vendor TEXT NOT NULL,
                amount TEXT NOT NULL,
                due_date TEXT NOT NULL,
                source_path TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS task_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                step TEXT NOT NULL,
                status TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")

    def log_event(self, task_id, step, status, detail):
        if not isinstance(detail, str):
            detail = json.dumps(detail, default=str, sort_keys=True)
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO task_events(task_id, step, status, detail) VALUES (?, ?, ?, ?)",
                (task_id, step, status, detail)
            )

    def get_events(self, task_id):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT step, status, detail, created_at FROM task_events "
                "WHERE task_id = ? ORDER BY event_id", (task_id,)
            ).fetchall()
        return [dict(row) for row in rows]
