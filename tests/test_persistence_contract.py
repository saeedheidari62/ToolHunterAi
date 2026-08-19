import json


def test_promotion_index_and_tool_file_are_consistent(tmp_path, monkeypatch):
    from backend.ai.tool_candidate_promoter import ToolCandidatePromoter

    knowledge_dir = tmp_path / "tools"
    knowledge_dir.mkdir()
    index_path = knowledge_dir / "tools_index.json"
    index_path.write_text(json.dumps({"tools": []}), encoding="utf-8")

    promoter = ToolCandidatePromoter(knowledge_dir=knowledge_dir)
    monkeypatch.setattr(
        promoter.technical_collector,
        "collect",
        lambda **_: {
            "success": True,
            "technical": {"power": "1000W"},
            "technical_sources": ["catalog"],
            "technical_confidence": "HIGH",
            "last_updated": "2026-08-19",
        },
    )
    monkeypatch.setattr(
        promoter.evidence_layer,
        "build",
        lambda **_: {
            "sufficient": True,
            "overall_confidence": 0.9,
            "sources": ["divar", "catalog"],
        },
    )
    monkeypatch.setattr(
        promoter.knowledge_builder,
        "normalize_technical",
        lambda data, sources: {"success": True, "technical": data},
    )
    monkeypatch.setattr(
        promoter.knowledge_builder,
        "build",
        lambda data: {"success": True, "knowledge": data, "errors": []},
    )

    candidate = {
        "status": "VALIDATED",
        "brand": "Makita",
        "model": "8281D",
        "variant": "WAE",
        "confidence": 0.94,
        "evidence": ["8281DWAE appears in the title"],
        "description": "Makita 8281DWAE",
        "market_data": {
            "valid": True,
            "sample_count": 2,
            "min_price": 100,
            "max_price": 120,
            "median_price": 110,
            "confidence": "MEDIUM",
        },
    }

    result = promoter.promote(candidate)
    assert result["status"] == "PROMOTED", result

    tool_path = knowledge_dir / "makita_8281d_wae.json"
    assert tool_path.exists()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert [item["id"] for item in index["tools"]] == ["makita_8281d_wae"]


def test_invalid_knowledge_index_blocks_promotion(tmp_path):
    from backend.ai.tool_candidate_promoter import ToolCandidatePromoter

    knowledge_dir = tmp_path / "tools"
    knowledge_dir.mkdir()
    (knowledge_dir / "tools_index.json").write_text("[]", encoding="utf-8")

    promoter = ToolCandidatePromoter(knowledge_dir=knowledge_dir)
    candidate = {
        "status": "VALIDATED",
        "brand": "Makita",
        "model": "8281D",
        "confidence": 0.94,
        "evidence": ["model evidence"],
        "market_data": {"valid": True, "sample_count": 2},
    }

    result = promoter.promote(candidate)
    assert result["status"] == "REJECTED", result
    assert "index" in result["reason"].lower()
