from backend.ad_analyzer import analyze_ad
from backend.decision_engine import make_decision


def test_buy_decision():
    sample_ad = {
        "tool_name": "Bosch_GBH_2_26",
        "asking_price": 8500000,
        "seller_type": "Personal",
        "has_test": True,
        "has_warranty": False,
        "condition": "Used"
    }

    analyzed = analyze_ad(sample_ad)
    result = make_decision(analyzed)

    assert result["decision"] in ["BUY", "REVIEW", "DON'T BUY"]