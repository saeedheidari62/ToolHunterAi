from datetime import datetime, timedelta, timezone
import sqlite3

from backend.alert_engine import AlertEngine
from backend.deal_events import DealEventLedger
from backend.deal_store import DealStore
from backend.deal_tracker import DealTracker


def test_alert_engine_excludes_events_older_than_48_hours(tmp_path):
    db = tmp_path / "alerts.sqlite3"
    tracker = DealTracker(DealStore(db), DealEventLedger(db))
    tracker.observe({"url": "https://divar.ir/v/old", "price": 9000000, "decision": "BUY"})
    tracker.observe({"url": "https://divar.ir/v/new", "price": 10000000, "decision": "BUY"})

    old = (datetime.now(timezone.utc) - timedelta(hours=49)).isoformat()
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE deal_events SET created_at=? WHERE listing_id=?", (old, "https://divar.ir/v/old"))
        conn.commit()

    alerts = AlertEngine(DealEventLedger(db)).recent(limit=10, min_priority=70)
    ids = [alert["listing_id"] for alert in alerts]

    assert "https://divar.ir/v/old" not in ids
    assert "https://divar.ir/v/new" in ids


def test_alert_engine_keeps_events_within_48_hours(tmp_path):
    db = tmp_path / "alerts.sqlite3"
    tracker = DealTracker(DealStore(db), DealEventLedger(db))
    tracker.observe({"url": "https://divar.ir/v/fresh", "price": 10000000, "decision": "BUY"})

    alerts = AlertEngine(DealEventLedger(db)).recent(limit=10, min_priority=70)

    assert [alert["listing_id"] for alert in alerts] == ["https://divar.ir/v/fresh"]
