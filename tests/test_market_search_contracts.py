from backend.divar_search_engine import DivarSearchEngine
from backend.market_price_engine import MarketPriceEngine
from backend.price_analyzer import analyze_price


def test_tool_id_resolves_to_market_friendly_query():
    engine = DivarSearchEngine()
    assert engine.build_query("makita_hr2470") == "Makita HR2470"
    assert engine.build_query("bosch_gbh_2_26", "DFR") == "Bosch GBH 2-26 DFR"


def test_filter_results_accepts_spaced_model_titles():
    engine = DivarSearchEngine()
    results = [
        {"title": "Makita HR 2470 ژاپن", "price": 8000000, "url": "https://divar.ir/v/1"},
        {"title": "Makita HR2470", "price": 8200000, "url": "https://divar.ir/v/2"},
        {"title": "Makita HR 2810", "price": 9000000, "url": "https://divar.ir/v/3"},
    ]
    filtered = engine.filter_results(results, "makita_hr2470")
    assert len(filtered) == 2


def test_market_engine_filters_invalid_prices_and_reports_effective_samples():
    result = MarketPriceEngine().calculate([100, 110, 120, 1000000, None, "bad"])
    assert result["valid"] is True
    assert result["sample_count"] == 3
    assert result["median_price"] == 110
    assert result["confidence"] == "HIGH"


def test_low_confidence_dynamic_market_falls_back_to_knowledge_base():
    tool = {"market": {"used_price_min": 800, "used_price_max": 1000}}
    dynamic = {
        "valid": True,
        "confidence": "LOW",
        "min_price": 700,
        "max_price": 700,
        "median_price": 700,
    }
    result = analyze_price(tool, 900, market_data=dynamic)
    assert result["market_source"] == "knowledge_base"
    assert result["price_status"] != "UNKNOWN"
