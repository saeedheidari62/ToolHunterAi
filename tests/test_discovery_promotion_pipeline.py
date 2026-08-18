from backend.evidence_layer import EvidenceLayer


def test_evidence_layer_normalizes_named_confidence_values():
    result = EvidenceLayer().build(
        discovery={"confidence": 0.94, "sources": ["divar"]},
        technical={"technical_confidence": "HIGH", "sources": ["manufacturer"]},
        market={"price_confidence": "MEDIUM", "sources": ["divar"]},
    )

    assert result["confidence_score"] > 0.7, result
    assert result["source_count"] == 2, result
    assert result["sufficient"] is True, result


def test_unknown_tool_api_promotes_only_validated_candidate(monkeypatch):
    from backend import api

    discovery = {
        "status": "CANDIDATE",
        "brand": "Makita",
        "model": "8281D",
        "variant": "WAE",
        "confidence": 0.94,
        "evidence": ["model found in advertisement title"],
    }
    validation = {
        "status": "VALIDATED",
        "brand": "Makita",
        "model": "8281D",
        "variant": "WAE",
        "confidence": 0.94,
        "evidence": ["model found in advertisement title"],
        "market_sample_count": 3,
        "market_data": {
            "used_price_min": 18000000,
            "used_price_max": 25000000,
            "median_price": 22000000,
            "sample_count": 3,
            "price_confidence": "HIGH",
            "sources": ["divar"],
        },
    }

    monkeypatch.setattr(api.matcher, "match_all", lambda _: [])
    monkeypatch.setattr(api.ai_tool_resolver, "resolve", lambda _: None)
    monkeypatch.setattr(api.ai_tool_discovery, "discover", lambda _: discovery)
    monkeypatch.setattr(api.ai_tool_candidate_validator, "validate", lambda *_args, **_kwargs: validation)
    monkeypatch.setattr(
        api.ai_tool_candidate_promoter,
        "promote",
        lambda candidate: {
            "status": "PROMOTED",
            "tool_id": "makita_8281d_wae",
            "market_sample_count": candidate["market_sample_count"],
        },
    )

    result = api.analyze_single_ad({
        "title": "پیچ گوشتی شارژی ماکیتا 8281DWAE",
        "description": "پک کامل سالم",
        "price": 22000000,
        "seller_type": "personal",
        "testing": False,
        "warranty": False,
        "condition": "used",
    })

    assert result["tool_candidate_promotion"]["status"] == "PROMOTED", result
    assert result["tool_candidate_promotion"]["market_sample_count"] == 3, result


def test_unknown_tool_api_does_not_promote_unverified_candidate(monkeypatch):
    from backend import api

    monkeypatch.setattr(api.matcher, "match_all", lambda _: [])
    monkeypatch.setattr(api.ai_tool_resolver, "resolve", lambda _: None)
    monkeypatch.setattr(api.ai_tool_discovery, "discover", lambda _: {
        "status": "CANDIDATE",
        "brand": "Makita",
        "model": "UNKNOWN",
        "confidence": 0.91,
        "evidence": ["weak marketplace evidence"],
    })
    monkeypatch.setattr(api.ai_tool_candidate_validator, "validate", lambda *_args, **_kwargs: {
        "status": "UNVERIFIED",
        "brand": "Makita",
        "model": "UNKNOWN",
        "confidence": 0.91,
        "market_sample_count": 1,
        "market_data": None,
        "evidence": ["weak marketplace evidence"],
    })

    def fail_if_called(_candidate):
        raise AssertionError("promotion must not run for an unverified candidate")

    monkeypatch.setattr(api.ai_tool_candidate_promoter, "promote", fail_if_called)

    result = api.analyze_single_ad({
        "title": "Makita UNKNOWN 9999",
        "description": "ابزار ناشناخته",
        "price": 1000000,
        "seller_type": "personal",
        "condition": "used",
    })

    assert result["tool_candidate_promotion"] is None, result
    assert result["tool_discovery_validation"]["status"] == "UNVERIFIED", result
