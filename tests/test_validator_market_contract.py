from backend.ai.tool_candidate_validator import ToolCandidateValidator


class FakeSearchEngine:
    def search(self, city, query, variant=None):
        return {"results": [
            {"title": "Makita 8281D A", "price": 100},
            {"title": "Makita 8281D B", "price": 1000},
            {"title": "Makita 8281D C", "price": 110},
            {"title": "Makita 8281D D", "price": 120},
        ]}

    def get_market_prices(self, search_result):
        return {
            "valid": True,
            "sample_count": 3,
            "min_price": 100,
            "max_price": 120,
            "median_price": 110,
        }


def test_validator_uses_effective_market_sample_count():
    candidate = {
        "brand": "Makita",
        "model": "8281D",
        "variant": "",
        "confidence": 0.94,
        "evidence": ["model found"],
    }
    result = ToolCandidateValidator(FakeSearchEngine(), min_samples=2).validate(candidate)
    assert result["status"] == "VALIDATED", result
    assert result["market_sample_count"] == 3, result
    assert result["market_data"]["sample_count"] == 3, result
