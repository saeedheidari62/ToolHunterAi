import sqlite3
from pathlib import Path


class WatchlistStore:
    """Persist user scan targets without coupling them to the scheduler."""

    def __init__(self, db_path=None):
        self.db_path = str(db_path or Path(__file__).resolve().parent.parent / "data" / "deal_history.sqlite3")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watchlists (
                    watch_id TEXT PRIMARY KEY,
                    cities_json TEXT NOT NULL,
                    tool_ids_json TEXT,
                    interval_seconds INTEGER NOT NULL,
                    top_n INTEGER,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL
                )
            """)

    def upsert(self, watch_id, cities, interval_seconds=3600, tool_ids=None, top_n=None, enabled=True, updated_at=None):
        import json
        from datetime import datetime, timezone
        updated_at = updated_at or datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO watchlists(watch_id,cities_json,tool_ids_json,interval_seconds,top_n,enabled,updated_at)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(watch_id) DO UPDATE SET
                    cities_json=excluded.cities_json,
                    tool_ids_json=excluded.tool_ids_json,
                    interval_seconds=excluded.interval_seconds,
                    top_n=excluded.top_n,
                    enabled=excluded.enabled,
                    updated_at=excluded.updated_at
            """, (watch_id, json.dumps(list(cities), ensure_ascii=False), json.dumps(list(tool_ids) if tool_ids else None), int(interval_seconds), top_n, int(bool(enabled)), updated_at))

    def get(self, watch_id):
        import json
        with self._connect() as conn:
            row = conn.execute("SELECT watch_id,cities_json,tool_ids_json,interval_seconds,top_n,enabled,updated_at FROM watchlists WHERE watch_id=?", (watch_id,)).fetchone()
        if not row:
            return None
        return {"watch_id": row[0], "cities": json.loads(row[1]), "tool_ids": json.loads(row[2]) if row[2] else None, "interval_seconds": row[3], "top_n": row[4], "enabled": bool(row[5]), "updated_at": row[6]}

    def list_enabled(self):
        with self._connect() as conn:
            ids = [row[0] for row in conn.execute("SELECT watch_id FROM watchlists WHERE enabled=1 ORDER BY watch_id")]
        return [self.get(watch_id) for watch_id in ids]
