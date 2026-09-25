from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path


class Store:
    def __init__(self, database: Path) -> None:
        self.database = database
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        with self.connect() as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_records_kind ON records(kind);
                CREATE INDEX IF NOT EXISTS idx_records_updated ON records(updated_at DESC);
                """
            )

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def add(self, kind: str, title: str, body: str, metadata: dict | None = None) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        with self.lock, self.connect() as db:
            cur = db.execute(
                "INSERT INTO records(kind,title,body,metadata,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                (kind[:40], title[:200], body, json.dumps(metadata or {}, ensure_ascii=False), now, now),
            )
            row_id = cur.lastrowid
        return self.get(row_id)

    def get(self, row_id: int) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT * FROM records WHERE id=?", (row_id,)).fetchone()
        if not row:
            raise KeyError(row_id)
        return self._row(row)

    def list(self, kind: str = "", query: str = "", limit: int = 100) -> list[dict]:
        sql, args = "SELECT * FROM records WHERE 1=1", []
        if kind:
            sql += " AND kind=?"
            args.append(kind)
        if query:
            sql += " AND (title LIKE ? OR body LIKE ?)"
            args.extend([f"%{query}%", f"%{query}%"])
        sql += " ORDER BY updated_at DESC LIMIT ?"
        args.append(max(1, min(limit, 500)))
        with self.connect() as db:
            return [self._row(row) for row in db.execute(sql, args)]

    @staticmethod
    def _row(row: sqlite3.Row) -> dict:
        item = dict(row)
        try:
            item["metadata"] = json.loads(item["metadata"])
        except json.JSONDecodeError:
            item["metadata"] = {}
        return item

