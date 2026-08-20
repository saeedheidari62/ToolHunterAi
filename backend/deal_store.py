import json
import sqlite3
from pathlib import Path


class DealStore:
    """Persistent SQLite storage for the latest deal snapshot per listing."""

    def __init__(self, db_path=None):
        self.db_path = str(db_path or Path(__file__).resolve().parent.parent / "data" / "deal_history.sqlite3")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS deal_snapshots (
                    listing_id TEXT PRIMARY KEY,
                    snapshot_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

    def get(self, listing_id):
        if not listing_id:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT snapshot_json FROM deal_snapshots WHERE listing_id = ?",
                (listing_id,),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, snapshot):
        listing_id = snapshot.get("listing_id") if isinstance(snapshot, dict) else None
        timestamp = snapshot.get("timestamp") if isinstance(snapshot, dict) else None
        if not listing_id or not timestamp:
            raise ValueError("snapshot must include listing_id and timestamp")
        payload = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO deal_snapshots(listing_id, snapshot_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(listing_id) DO UPDATE SET
                    snapshot_json = excluded.snapshot_json,
                    updated_at = excluded.updated_at
                """,
                (listing_id, payload, timestamp),
            )

    def count(self):
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM deal_snapshots").fetchone()[0]
