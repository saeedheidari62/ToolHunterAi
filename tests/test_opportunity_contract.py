from backend.opportunity_contract import build_opportunity_contract


def test_buy_now_requires_safe_decision_and_risk():
    result = build_opportunity_contract({
        "decision": "BUY",
        "risk_score": 30,
        "opportunity_score": 82,
        "price_difference_percent": -18,
        "tool": "bosch_gbh_2_26",
        "has_test": True,
        "url": "https://divar.ir/v/1",
    })

    assert result["status"] == "BUY_NOW"
    assert "Price is 18.0% below market." in result["evidence"]
    assert "Tool identity matched." in result["evidence"]
    assert "Testing is available." in result["evidence"]


def test_high_risk_cannot_be_buy_now():
    result = build_opportunity_contract({
        "decision": "BUY",
        "risk_score": 76,
        "opportunity_score": 90,
    })

    assert result["status"] == "REJECT"


def test_review_is_exposed_as_review():
    result = build_opportunity_contract({
        "decision": "REVIEW",
        "risk_score": 55,
        "opportunity_score": 55,
    })

    assert result["status"] == "REVIEW"
