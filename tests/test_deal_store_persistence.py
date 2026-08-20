from backend.deal_store import DealStore
from backend.deal_tracker import DealTracker


def test_deal_store_persists_latest_snapshot(tmp_path):
    db = tmp_path / "deals.sqlite3"
    first = DealTracker(DealStore(db))

    item = {"url": "https://divar.ir/v/1", "price": 12000000, "decision": "REVIEW"}
    assert first.observe(item)["event"] == "NEW_DEAL"

    second = DealTracker(DealStore(db))
    result = second.observe({"url": "https://divar.ir/v/1", "price": 9000000, "decision": "BUY"})

    assert result["event"] == "PRICE_DROP"
    assert "PRICE_DROP" in result["events"]
    assert "DECISION_UPGRADE" in result["events"]
    assert result["previous"]["price"] == 12000000
    assert second.get("https://divar.ir/v/1")["price"] == 9000000


def test_deal_store_counts_unique_listings(tmp_path):
    store = DealStore(tmp_path / "deals.sqlite3")
    tracker = DealTracker(store)
    tracker.observe({"url": "https://divar.ir/v/1", "price": 100})
    tracker.observe({"url": "https://divar.ir/v/2", "price": 200})
    tracker.observe({"url": "https://divar.ir/v/1", "price": 90})
    assert store.count() == 2
