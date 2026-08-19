import json

from backend.ai.tool_candidate_promoter import ToolCandidatePromoter


def _candidate():
    return {
        "status": "VALIDATED", "brand": "TestBrand", "model": "Model100", "variant": "",
        "confidence": 0.95, "evidence": ["marketplace model evidence"],
        "market_data": {"valid": True, "sample_count": 2, "median_price": 1000, "min_price": 900, "max_price": 1100, "confidence": "MEDIUM"},
        "description": "Test tool",
    }


def test_duplicate_promotion_is_idempotent(tmp_path, monkeypatch):
    promoter = ToolCandidatePromoter(knowledge_dir=tmp_path, min_samples=2)
    monkeypatch.setattr(promoter.evidence_layer, "build", lambda **kwargs: {"sufficient": True, "sources": ["divar"]})
    monkeypatch.setattr(promoter.technical_collector, "collect", lambda **kwargs: {"success": True, "technical": {}, "technical_sources": [], "technical_confidence": "NONE"})
    monkeypatch.setattr(promoter.knowledge_builder, "normalize_technical", lambda data, sources: {"success": True, "technical": data})
    monkeypatch.setattr(promoter.knowledge_builder, "build", lambda data: {"success": True, "errors": []})
    first = promoter.promote(_candidate()); second = promoter.promote(_candidate())
    assert first["status"] == "PROMOTED"
    assert second["status"] == "EXISTS"
    index = json.loads((tmp_path / "tools_index.json").read_text(encoding="utf-8"))
    assert len(index["tools"]) == 1


def test_rejected_candidate_does_not_persist(tmp_path):
    promoter = ToolCandidatePromoter(knowledge_dir=tmp_path, min_samples=2)
    candidate = _candidate(); candidate["market_data"]["sample_count"] = 1
    result = promoter.promote(candidate)
    assert result["status"] == "REJECTED"
    assert not (tmp_path / "tools_index.json").exists()
    assert not list(tmp_path.glob("*.json"))
