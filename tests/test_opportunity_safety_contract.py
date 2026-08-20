from backend.opportunity_engine import OpportunityEngine


def test_unsafe_ads_are_blocked_and_not_best_choice():
    engine = OpportunityEngine()
    result = engine.rank([
        {"url": "https://divar.ir/v/unsafe", "decision": "BUY", "buy_score": 99, "risk_score": 90},
        {"url": "https://divar.ir/v/safe", "decision": "REVIEW", "buy_score": 75, "risk_score": 35},
    ])

    unsafe = next(item for item in result["opportunities"] if item["url"].endswith("unsafe"))
    assert unsafe["opportunity_status"] == "BLOCKED"
    assert result["best_opportunity"]["url"].endswith("safe")
