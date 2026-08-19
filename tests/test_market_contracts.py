from backend.divar_search_engine import DivarSearchEngine
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


def test_low_confidence_dynamic_market_does_not_override_static_baseline():
    tool = {"market": {"used_price_min": 8, "used_price_max": 12}}
    result = analyze_price(
        tool,
        10,
        market_data={
            "valid": True,
            "confidence": "LOW",
            "min_price": 1,
            "max_price": 2,
            "median_price": 1.5,
        },
    )
    assert result["market_source"] == "knowledge_base"
    assert any("LOW confidence" in reason for reason in result["price_reason"])


def test_invalid_market_data_returns_unknown_price_status():
    tool = {"market": {"used_price_min": 8, "used_price_max": 12}}
    result = analyze_price(tool, 10, market_data={"valid": True, "confidence": "HIGH"})
    assert result["price_status"] == "UNKNOWN"
    assert result["price_difference_percent"] is None


def test_divar_search_resolves_tool_id_to_market_name():
    engine = DivarSearchEngine()
    assert engine.build_query("makita_hr2470") == "Makita HR2470"
    assert engine.build_query("بوش ۲۶") == "Bosch GBH 2-26"


def test_divar_search_normalizes_supported_cities_without_fallback():
    engine = DivarSearchEngine()
    assert engine._normalize_city("تهران") == "tehran"
    assert engine._normalize_city("Karaj") == "karaj"
    assert engine._normalize_city("قم") == "qom"
    assert engine._normalize_city("unknown-city") == ""


def test_divar_search_variant_query_is_explicit():
    engine = DivarSearchEngine()
    assert engine.build_query("bosch_gbh_2_26", variant="DRE") == "Bosch GBH 2-26 DRE"
