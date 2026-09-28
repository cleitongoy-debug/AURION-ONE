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
                CREATE TABLE IF NOT EXISTS dedication_events (
                    event_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    received_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_dedication_time ON dedication_events(occurred_at);
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

    def put_dedication(self, events: list[dict]) -> int:
        allowed = {"session", "progress", "milestone", "evidence"}
        now = datetime.now(timezone.utc).isoformat()
        accepted = 0
        with self.lock, self.connect() as db:
            for event in events[:200]:
                if not isinstance(event, dict):
                    continue
                eid, source, kind = (str(event.get(k, "")) for k in ("id", "source", "kind"))
                if not (8 <= len(eid) <= 100 and source in {"poco", "pc"} and kind in allowed):
                    continue
                stamp = str(event.get("at", ""))
                try:
                    datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                except ValueError:
                    continue
                if kind == "session":
                    start, end = event.get("start"), event.get("end")
                    if not (isinstance(start, (int, float)) and isinstance(end, (int, float))
                            and 0 < end - start <= 24 * 3600 * 1000):
                        continue
                if kind == "progress":
                    percentage = event.get("percent")
                    if not (isinstance(percentage, (int, float)) and 0 <= percentage <= 100
                            and str(event.get("course", "")).strip()):
                        continue
                payload = json.dumps(event, ensure_ascii=False)
                if len(payload) > 12000:
                    continue
                accepted += db.execute(
                    "INSERT OR IGNORE INTO dedication_events VALUES(?,?,?,?,?,?)",
                    (eid, source, kind, stamp, payload, now),
                ).rowcount
        return accepted

    def dedication(self) -> list[dict]:
        with self.connect() as db:
            rows = db.execute("SELECT payload FROM dedication_events ORDER BY occurred_at, event_id").fetchall()
        return [json.loads(row["payload"]) for row in rows]

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
