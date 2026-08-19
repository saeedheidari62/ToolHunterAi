from backend.divar_search_engine import DivarSearchEngine
from backend.price_analyzer import analyze_price


def test_search_query_uses_catalog_name_for_tool_id():
    engine = DivarSearchEngine()
    assert engine.build_query("makita_hr2470") == "Makita HR2470"


def test_search_query_preserves_variant():
    engine = DivarSearchEngine()
    assert engine.build_query("bosch_gbh_2_26", "DFR") == "Bosch GBH 2-26 DFR"


def test_weak_dynamic_market_falls_back_to_knowledge_base():
    tool = {"market": {"used_price_min": 8_000_000, "used_price_max": 9_500_000}}
    market = {
        "valid": True,
        "confidence": "LOW",
        "sample_count": 1,
        "min_price": 7_000_000,
        "median_price": 7_000_000,
        "max_price": 7_000_000,
    }
    result = analyze_price(tool, 8_000_000, market)
    assert result["market_source"] == "knowledge_base"


def test_strong_dynamic_market_is_used():
    tool = {"market": {"used_price_min": 8_000_000, "used_price_max": 9_500_000}}
    market = {
        "valid": True,
        "confidence": "HIGH",
        "sample_count": 3,
        "min_price": 8_000_000,
        "median_price": 8_500_000,
        "max_price": 9_000_000,
    }
    result = analyze_price(tool, 8_500_000, market)
    assert result["market_source"] == "dynamic"
