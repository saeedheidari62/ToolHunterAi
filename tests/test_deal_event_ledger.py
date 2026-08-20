from backend.deal_events import DealEventLedger
from backend.deal_store import DealStore
from backend.deal_tracker import DealTracker


def test_event_ledger_persists_and_prioritizes_upgrade(tmp_path):
    db = tmp_path / "deals.sqlite3"
    tracker = DealTracker(DealStore(db), DealEventLedger(db))
    tracker.observe({"url": "https://divar.ir/v/1", "price": 12000000, "decision": "REVIEW"})
    result = tracker.observe({"url": "https://divar.ir/v/1", "price": 9000000, "decision": "BUY"})

    assert result["event"] == "PRICE_DROP"
    assert result["alert"]["priority"] == 100

    ledger = DealEventLedger(db)
    recent = ledger.recent()
    assert len(recent) == 2
    assert recent[0]["priority"] == 100
    assert recent[0]["event"] == "PRICE_DROP"
