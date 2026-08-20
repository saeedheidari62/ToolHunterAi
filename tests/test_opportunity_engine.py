from backend.opportunity_engine import OpportunityEngine


def test_opportunity_score_prefers_strong_buy_with_good_price_and_low_risk():
    engine = OpportunityEngine()
    strong = engine.score({
        "decision": "BUY",
        "buy_score": 95,
        "risk_score": 20,
        "ad_score": 90,
        "price_difference_percent": -25,
        "has_test": True,
        "has_warranty": True,
    })
    weak = engine.score({
        "decision": "REVIEW",
        "buy_score": 65,
        "risk_score": 55,
        "ad_score": 55,
        "price_difference_percent": 5,
    })
    assert strong > weak
    assert 0 <= strong <= 100


def test_rank_adds_status_and_respects_limit():
    engine = OpportunityEngine()
    result = engine.rank([
        {"decision": "BUY", "buy_score": 95, "risk_score": 20, "ad_score": 90, "price_difference_percent": -20},
        {"decision": "REVIEW", "buy_score": 65, "risk_score": 55, "ad_score": 55, "price_difference_percent": 5},
    ], limit=1)
    assert result["total"] == 1
    assert result["best_opportunity"] is not None
    assert result["opportunities"][0]["opportunity_status"] in {"OPPORTUNITY", "WATCH", "LOW_VALUE"}
