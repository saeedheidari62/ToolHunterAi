from backend.deal_events import DealEventLedger
from backend.deal_store import DealStore
from backend.deal_tracker import DealTracker
from backend.web_app import app


def test_alerts_endpoint_returns_priority_ordered_actionable_events(tmp_path, monkeypatch):
    db = tmp_path / "alerts.sqlite3"
    tracker = DealTracker(DealStore(db), DealEventLedger(db))
    tracker.observe({"url": "https://divar.ir/v/1", "price": 12000000, "decision": "REVIEW"})
    tracker.observe({"url": "https://divar.ir/v/1", "price": 9000000, "decision": "BUY"})

    monkeypatch.setattr("backend.web_app.alert_engine", __import__("backend.alert_engine", fromlist=["AlertEngine"]).AlertEngine(DealEventLedger(db)))
    response = app.test_client().get("/alerts?limit=5&min_priority=70")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["alerts"]
    assert payload["alerts"][0]["priority"] == 100
    assert payload["alerts"][0]["event"] == "PRICE_DROP"
    assert "label" in payload["alerts"][0]
