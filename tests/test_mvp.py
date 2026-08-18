from backend.api import analyze_single_ad
from backend.price_analyzer import analyze_price
from backend.tool_variant_matcher import ToolVariantMatcher


def run(name, ad, expected_tool=None, expected_error=None):
    result = analyze_single_ad(ad)
    if expected_error:
        assert result.get("error") == expected_error, (name, result)
    else:
        assert "error" not in result, (name, result)
        assert result.get("tool") == expected_tool, (name, result)
        assert result.get("decision") in {"BUY", "REVIEW", "DON'T BUY"}, (name, result)
        assert 0 <= result.get("buy_score", -1) <= 100, (name, result)
        assert 0 <= result.get("risk_score", -1) <= 100, (name, result)
        assert result.get("decision_reason"), (name, result)
        assert result.get("next_action"), (name, result)
    print("PASS:", name)


run(
    "Bosch GBH 2-26",
    {
        "title": "Bosch GBH 2-26",
        "description": "دریل بتن کن بوش GBH 2-26 سالم با امکان تست",
        "price": 8500000,
        "seller_type": "personal",
        "testing": True,
        "warranty": False,
        "condition": "used"
    },
    "bosch_gbh_2_26"
)

run(
    "Bosch GSH500",
    {
        "title": "Bosch GSH500",
        "description": "بتن کن بوش مدل GSH500 سالم",
        "price": 9000000,
        "seller_type": "personal",
        "testing": False,
        "warranty": False,
        "condition": "used"
    },
    "bosch_gsh500"
)

run(
    "Makita HR2470",
    {
        "title": "Makita HR2470",
        "description": "بتن کن ماکیتا 2470 سالم",
        "price": 8000000,
        "seller_type": "personal",
        "testing": True,
        "warranty": False,
        "condition": "used"
    },
    "makita_hr2470"
)


def test_variant_detection():
    matcher = ToolVariantMatcher()
    tool_id = "bosch_gbh_2_26"

    assert matcher.detect("Bosch GBH 2-26 DRE Professional", tool_id) == "DRE"
    assert matcher.detect("بتن کن بوش GBH 2-26 DFR", tool_id) == "DFR"
    assert matcher.detect("دریل بوش GBH 2-26 در حد نو", tool_id) is None
    print("PASS: variant detection")


def test_low_confidence_market_fallback():
    tool = {
        "market": {
            "used_price_min": 8000000,
            "used_price_max": 9500000
        }
    }

    result = analyze_price(
        tool,
        9000000,
        market_data={
            "valid": True,
            "sample_count": 1,
            "min_price": 27500000,
            "max_price": 27500000,
            "median_price": 27500000,
            "confidence": "LOW"
        }
    )

    assert result["price_status"] != "VERY_HIGH_PRICE", result
    assert result["price_difference_percent"] is not None, result
    print("PASS: low-confidence market fallback")


def test_medium_confidence_dynamic_market():
    tool = {
        "market": {
            "used_price_min": 8000000,
            "used_price_max": 9500000
        }
    }

    result = analyze_price(
        tool,
        14900000,
        market_data={
            "valid": True,
            "sample_count": 2,
            "min_price": 12000000,
            "max_price": 14900000,
            "median_price": 13450000,
            "confidence": "MEDIUM"
        }
    )

    assert result["price_status"] == "HIGH_PRICE", result
    assert result["price_difference_percent"] == 10.78, result
    print("PASS: medium-confidence dynamic market")


test_variant_detection()
test_low_confidence_market_fallback()
test_medium_confidence_dynamic_market()
print("ALL REGRESSION TESTS PASSED")
