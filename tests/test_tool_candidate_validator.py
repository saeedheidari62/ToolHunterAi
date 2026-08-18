from backend.ai.tool_candidate_validator import ToolCandidateValidator


class FakeSearch:
    def __init__(self, results):
        self.results = results

    def search(self, city, query):
        return {"results": self.results}


def test_candidate_validated_by_multiple_market_listings():
    validator = ToolCandidateValidator(
        FakeSearch([
            {"title": "Makita 8281D WAE Japan", "price": 5000000},
            {"title": "پیچ گوشتی Makita 8281DWAE", "price": 5500000},
        ])
    )
    result = validator.validate({
        "brand": "Makita",
        "model": "8281D",
        "variant": "WAE",
        "confidence": 0.94,
        "evidence": ["8281DWAE in title"],
    })
    assert result["status"] == "VALIDATED"
    assert result["market_sample_count"] == 2


def test_candidate_stays_unverified_with_insufficient_evidence():
    validator = ToolCandidateValidator(
        FakeSearch([
            {"title": "Makita 8281D WAE", "price": 5000000},
        ])
    )
    result = validator.validate({
        "brand": "Makita",
        "model": "8281D",
        "variant": "WAE",
        "confidence": 0.94,
        "evidence": ["8281DWAE in title"],
    })
    assert result["status"] == "UNVERIFIED"
    assert result["market_sample_count"] == 1


def test_low_confidence_candidate_is_rejected():
    validator = ToolCandidateValidator(FakeSearch([]))
    result = validator.validate({
        "brand": "Makita",
        "model": "8281D",
        "variant": "WAE",
        "confidence": 0.60,
        "evidence": [],
    })
    assert result["status"] == "REJECTED"
