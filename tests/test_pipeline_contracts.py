from backend.ai.tool_candidate_promoter import ToolCandidatePromoter


def test_promoter_preserves_validator_technical_data(tmp_path):
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    (tools_dir / "tools_index.json").write_text('{"tools": []}', encoding="utf-8")

    candidate = {
        "status": "VALIDATED",
        "brand": "Makita",
        "model": "8281D",
        "variant": "WAE",
        "confidence": 0.94,
        "evidence": ["model appears in listing"],
        "technical_data": {"voltage_v": 14.4, "battery_type": "Ni-Cd"},
        "technical_sources": ["manufacturer"],
        "market_sample_count": 2,
        "market_data": {
            "used_price_min": 18000000,
            "used_price_max": 25000000,
            "median_price": 22000000,
            "sample_count": 2,
            "price_confidence": "MEDIUM",
            "sources": ["divar"],
        },
    }

    result = ToolCandidatePromoter(tools_dir).promote(candidate)

    assert result["status"] == "PROMOTED", result
    import json
    saved = json.loads((tools_dir / "makita_8281d_wae.json").read_text(encoding="utf-8"))
    assert saved["technical"]["voltage"] == 14.4
    assert saved["technical"]["battery"] == "Ni-Cd"
    assert "manufacturer" in saved["technical"]["sources"]
