from backend.deal_tracker import DealTracker


def item(price=12000000, decision="REVIEW", risk=50):
    return {
        "token": "abc123",
        "url": "https://divar.ir/v/abc123",
        "tool_id": "bosch_gbh_2_26",
        "tool_name": "Bosch GBH 2-26",
        "city": "tehran",
        "price": price,
        "market_price": 14500000,
        "buy_score": 78,
        "risk_score": risk,
        "decision": decision,
        "opportunity_score": 72,
    }


def test_new_listing_emits_new_deal():
    tracker = DealTracker()
    result = tracker.observe(item())
    assert result["event"] == "NEW_DEAL"
    assert result["snapshot"]["listing_id"] == "abc123"
    assert result["snapshot"]["url"].endswith("abc123")


def test_price_drop_emits_price_drop():
    tracker = DealTracker()
    tracker.observe(item(price=12000000))
    result = tracker.observe(item(price=9000000))
    assert result["event"] == "PRICE_DROP"
    assert "PRICE_DROP" in result["events"]
    assert result["previous"]["price"] == 12000000
    assert result["snapshot"]["price"] == 9000000


def test_decision_change_and_risk_change_are_detected():
    tracker = DealTracker()
    tracker.observe(item(decision="REVIEW", risk=50))
    result = tracker.observe(item(decision="BUY", risk=30))
    assert "DECISION_UPGRADE" in result["events"]
    assert "RISK_CHANGE" in result["events"]


def test_unchanged_listing_does_not_emit_noise():
    tracker = DealTracker()
    tracker.observe(item())
    result = tracker.observe(item())
    assert result["event"] == "UNCHANGED"
    assert result["events"] == []
