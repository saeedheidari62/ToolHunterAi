import sqlite3
from pathlib import Path


class NotificationLedger:
    """Persistent idempotency ledger for notification delivery."""

    def __init__(self, path="data/notification_ledger.sqlite3"):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS deliveries (event_id TEXT PRIMARY KEY, status TEXT NOT NULL)")
            conn.commit()

    def was_sent(self, event_id):
        with sqlite3.connect(self.path) as conn:
            row = conn.execute("SELECT 1 FROM deliveries WHERE event_id=? AND status='SENT'", (str(event_id),)).fetchone()
            return row is not None

    def mark_sent(self, event_id):
        with sqlite3.connect(self.path) as conn:
            conn.execute("INSERT OR REPLACE INTO deliveries(event_id,status) VALUES(?, 'SENT')", (str(event_id),))
            conn.commit()
