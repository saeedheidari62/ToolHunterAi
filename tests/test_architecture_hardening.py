from pathlib import Path


def test_legacy_app_delegates_to_api_pipeline():
    from backend import app
    from backend import api

    assert app.analyze_single_ad is api.analyze_single_ad


def test_candidate_validator_never_defaults_unknown_city_to_tehran():
    from backend.ai.tool_candidate_validator import ToolCandidateValidator

    class Search:
        def search(self, city, query, variant=None):
            raise AssertionError("market search must not run for an unsupported city")

    validator = ToolCandidateValidator(Search())
    result = validator.validate(
        {
            "brand": "Makita",
            "model": "8281D",
            "confidence": 0.95,
            "evidence": ["title"],
        },
        city="unknown-city",
    )

    assert result["status"] == "UNVERIFIED"
    assert "city" in result["reason"].lower()


def test_promoter_uses_project_root_for_default_knowledge_path():
    from backend.ai.tool_candidate_promoter import ToolCandidatePromoter

    promoter = ToolCandidatePromoter()
    expected = Path(__file__).resolve().parents[1] / "knowledge_base" / "tools"
    assert promoter.knowledge_dir == expected


def test_promoter_can_mark_market_unavailable_without_fake_prices():
    from backend.ai.tool_candidate_promoter import ToolCandidatePromoter

    promoter = ToolCandidatePromoter()
    data = promoter._build_default_knowledge(
        {
            "brand": "TestBrand",
            "model": "Test123",
            "confidence": 0.9,
            "evidence": ["observed"],
            "market_sample_count": 0,
            "market_data": None,
        }
    )

    assert data["market"]["status"] == "unavailable"
    assert data["market"]["used_price_min"] is None
    assert data["market"]["used_price_max"] is None
