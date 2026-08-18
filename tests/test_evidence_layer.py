from backend.evidence_layer import EvidenceLayer


def test_unified_evidence_combines_sources_and_scores_coverage():
    result = EvidenceLayer().build(
        discovery={"confidence": 0.9, "sources": ["divar"]},
        technical={"confidence": 0.8, "sources": ["manufacturer"]},
        market={"price_confidence": 0.7, "sources": ["divar"]},
    )

    assert result["components"] == {
        "discovery": True,
        "technical": True,
        "market": True,
    }
    assert result["sources"] == ["divar", "manufacturer"]
    assert result["source_count"] == 2
    assert result["overall_confidence"] > 0.7
    assert result["sufficient"] is True


def test_empty_evidence_is_not_sufficient():
    result = EvidenceLayer().build()
    assert result["source_count"] == 0
    assert result["sufficient"] is False
