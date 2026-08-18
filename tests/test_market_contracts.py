from backend.market_price_engine import MarketPriceEngine
from backend.price_analyzer import analyze_price


def test_market_engine_reports_confidence_from_effective_samples():
    result = MarketPriceEngine().calculate([10, 11, 12])
    assert result["valid"] is True
    assert result["sample_count"] == 3
    assert result["confidence"] == "HIGH"


def test_price_analyzer_exposes_dynamic_market_source():
    tool = {"market": {"used_price_min": 8, "used_price_max": 12}}
    result = analyze_price(
        tool,
        10,
        market_data={
            "valid": True,
            "confidence": "HIGH",
            "min_price": 9,
            "max_price": 11,
            "median_price": 10,
        },
    )
    assert result["market_source"] == "dynamic"


def test_price_analyzer_marks_static_fallback_explicitly():
    tool = {"market": {"used_price_min": 8, "used_price_max": 12}}
    result = analyze_price(tool, 10, market_data=None)
    assert result["market_source"] == "knowledge_base"
