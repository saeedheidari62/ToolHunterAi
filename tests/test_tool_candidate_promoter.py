from backend.ai.tool_candidate_promoter import ToolCandidatePromoter


def validated_candidate(**overrides):
    candidate = {
        "status": "VALIDATED",
        "brand": "Makita",
        "model": "8281D",
        "variant": "WAE",
        "confidence": 0.94,
        "evidence": ["market listing 1", "market listing 2"],
        "market_sample_count": 2,
    }
    candidate.update(overrides)
    return candidate


def test_rejects_unvalidated_candidate(tmp_path):
    promoter = ToolCandidatePromoter(tmp_path / "tools")
    result = promoter.promote({"status": "UNVERIFIED", "brand": "Makita", "model": "8281D"})
    assert result["status"] == "REJECTED"


def test_rejects_low_confidence_candidate(tmp_path):
    promoter = ToolCandidatePromoter(tmp_path / "tools")
    result = promoter.promote(validated_candidate(confidence=0.79))
    assert result["status"] == "REJECTED"


def test_rejects_insufficient_market_evidence(tmp_path):
    promoter = ToolCandidatePromoter(tmp_path / "tools")
    result = promoter.promote(validated_candidate(market_sample_count=1))
    assert result["status"] == "REJECTED"


def test_rejects_candidate_without_evidence(tmp_path):
    promoter = ToolCandidatePromoter(tmp_path / "tools")
    result = promoter.promote(validated_candidate(evidence=[]))
    assert result["status"] == "REJECTED"


def test_promotes_validated_candidate_and_updates_index(tmp_path):
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    (tools_dir / "tools_index.json").write_text('{"tools": []}', encoding="utf-8")

    promoter = ToolCandidatePromoter(tools_dir)
    result = promoter.promote(validated_candidate())

    assert result["status"] == "PROMOTED"
    assert result["tool_id"] == "makita_8281d_wae"
    assert (tools_dir / "makita_8281d_wae.json").exists()
    index = (tools_dir / "tools_index.json").read_text(encoding="utf-8")
    assert "makita_8281d_wae" in index


def test_does_not_overwrite_existing_tool(tmp_path):
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    (tools_dir / "tools_index.json").write_text('{"tools": []}', encoding="utf-8")
    (tools_dir / "makita_8281d_wae.json").write_text('{"keep": true}', encoding="utf-8")

    promoter = ToolCandidatePromoter(tools_dir)
    result = promoter.promote(validated_candidate())

    assert result["status"] == "EXISTS"
    assert '"keep": true' in (tools_dir / "makita_8281d_wae.json").read_text(encoding="utf-8")
