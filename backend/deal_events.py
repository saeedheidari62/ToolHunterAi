import json
import sqlite3
from pathlib import Path


class DealEventLedger:
    """Persist deal events and expose alert-ready priority ordering."""

    PRIORITY = {
        "DECISION_UPGRADE": 100,
        "PRICE_DROP": 90,
        "NEW_DEAL": 70,
        "RISK_CHANGE": 50,
        "PRICE_RISE": 30,
        "DECISION_CHANGE": 20,
    }

    def __init__(self, db_path=None):
        self.db_path = str(db_path or Path(__file__).resolve().parent.parent / "data" / "deal_history.sqlite3")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS deal_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id TEXT NOT NULL,
                    event TEXT NOT NULL,
                    events_json TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    previous_json TEXT,
                    priority INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

    def record(self, result):
        if not result or result.get("event") in (None, "UNCHANGED", "IGNORED"):
            return None
        snapshot = result.get("snapshot") or {}
        event = result.get("event")
        created_at = snapshot.get("timestamp", "")
        priority = max((self.PRIORITY.get(name, 0) for name in result.get("events", [event])), default=0)
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO deal_events
                (listing_id,event,events_json,snapshot_json,previous_json,priority,created_at)
                VALUES (?,?,?,?,?,?,?)""",
                (snapshot.get("listing_id", ""), event,
                 json.dumps(result.get("events", [event]), ensure_ascii=False),
                 json.dumps(snapshot, ensure_ascii=False),
                 json.dumps(result.get("previous"), ensure_ascii=False) if result.get("previous") else None,
                 priority, created_at),
            )
            return {"id": cursor.lastrowid, "listing_id": snapshot.get("listing_id"), "event": event, "priority": priority, "created_at": created_at}

    def record_many(self, results):
        return [event for result in results if (event := self.record(result))]

    def recent(self, limit=20):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id,listing_id,event,priority,created_at FROM deal_events ORDER BY priority DESC, id DESC LIMIT ?",
                (max(1, min(int(limit), 100)),),
            ).fetchall()
        return [dict(zip(("id", "listing_id", "event", "priority", "created_at"), row)) for row in rows]
