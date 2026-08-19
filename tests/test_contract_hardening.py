from backend.price_analyzer import analyze_price
from backend.ai.tool_candidate_promoter import ToolCandidatePromoter


def test_dynamic_market_requires_valid_range_and_effective_samples():
    tool = {"market": {"used_price_min": 8000000, "used_price_max": 9500000}}
    weak = analyze_price(
        tool,
        9000000,
        market_data={
            "valid": True,
            "sample_count": 2,
            "min_price": 12000000,
            "max_price": 14900000,
            "median_price": 30000000,
            "confidence": "MEDIUM",
        },
    )
    assert weak["market_source"] == "knowledge_base", weak


def test_low_sample_dynamic_market_uses_static_baseline():
    tool = {"market": {"used_price_min": 8000000, "used_price_max": 9500000}}
    result = analyze_price(
        tool,
        9000000,
        market_data={
            "valid": True,
            "sample_count": 1,
            "min_price": 8000000,
            "max_price": 8000000,
            "median_price": 8000000,
            "confidence": "MEDIUM",
        },
    )
    assert result["market_source"] == "knowledge_base", result
    assert any("static market baseline" in reason for reason in result["price_reason"]), result


def test_promotion_uses_market_data_sample_count(tmp_path):
    promoter = ToolCandidatePromoter(knowledge_dir=tmp_path, min_samples=2)
    candidate = {
        "status": "VALIDATED",
        "brand": "TestBrand",
        "model": "X100",
        "confidence": 0.95,
        "evidence": ["model appears in listing title"],
        "market_sample_count": 99,
        "market_data": {
            "valid": True,
            "sample_count": 1,
            "min_price": 100,
            "max_price": 120,
            "median_price": 110,
            "confidence": "LOW",
        },
    }
    result = promoter.promote(candidate)
    assert result["status"] == "REJECTED", result
    assert "Insufficient marketplace evidence" in result["reason"], result


def test_promotion_rejects_invalid_market_data(tmp_path):
    promoter = ToolCandidatePromoter(knowledge_dir=tmp_path, min_samples=2)
    candidate = {
        "status": "VALIDATED",
        "brand": "TestBrand",
        "model": "X101",
        "confidence": 0.95,
        "evidence": ["model appears in listing title"],
        "market_data": {
            "valid": False,
            "sample_count": 5,
            "min_price": 100,
            "max_price": 120,
            "median_price": 110,
            "confidence": "HIGH",
        },
    }
    result = promoter.promote(candidate)
    assert result["status"] == "REJECTED", result
    assert "Validated market data" in result["reason"], result
