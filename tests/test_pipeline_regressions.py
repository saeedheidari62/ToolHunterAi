def test_promoted_candidate_is_analyzed_in_same_request(monkeypatch):
    from backend import api

    state = {"promoted": False}

    monkeypatch.setattr(api.matcher, "match_all", lambda _: ["makita_8281d"] if state["promoted"] else [])
    monkeypatch.setattr(api.matcher, "reload", lambda: None)
    monkeypatch.setattr(
        api.ai_tool_resolver,
        "resolve",
        lambda _: None,
    )
    monkeypatch.setattr(
        api.ai_tool_discovery,
        "discover",
        lambda _: {
            "status": "CANDIDATE",
            "brand": "Makita",
            "model": "8281D",
            "variant": "WAE",
            "confidence": 0.94,
            "evidence": ["8281DWAE appears in the title"],
        },
    )
    monkeypatch.setattr(
        api.ai_tool_candidate_validator,
        "validate",
        lambda discovery, city=None: {
            "status": "VALIDATED",
            "brand": "Makita",
            "model": "8281D",
            "variant": "WAE",
            "confidence": 0.94,
            "evidence": discovery["evidence"],
            "market_sample_count": 2,
            "market_data": {"valid": True, "sample_count": 2},
        },
    )

    def promote(candidate):
        state["promoted"] = True
        return {"status": "PROMOTED", "tool_id": "makita_8281d_wae", "file": "makita_8281d_wae.json"}

    monkeypatch.setattr(api.ai_tool_candidate_promoter, "promote", promote)
    monkeypatch.setattr(api, "get_dynamic_market_data", lambda *args, **kwargs: None)
    monkeypatch.setattr(api, "analyze_ad", lambda _: {"ad_score": 85, "analysis": []})
    monkeypatch.setattr(
        api,
        "make_decision",
        lambda _: {
            "decision": "REVIEW",
            "buy_score": 70,
            "risk_score": 40,
            "decision_reason": "Promoted candidate analyzed",
            "next_action": "Inspect tool",
        },
    )

    result = api.analyze_single_ad({
        "title": "پیچ گوشتی شارژی ماکیتا 8281DWAE ژاپن اصل",
        "description": "دستگاه سالم",
        "price": 5000000,
        "seller_type": "personal",
        "testing": False,
        "warranty": False,
        "condition": "used",
    })

    assert result.get("error") is None, result
    assert result["tool"] == "makita_8281d_wae", result
    assert result["tool_candidate_promotion"]["status"] == "PROMOTED", result


def test_unknown_city_does_not_silently_use_tehran(monkeypatch):
    from backend import api

    calls = []

    def fake_search(city, query, variant=None):
        calls.append(city)
        return {"results": []}

    monkeypatch.setattr(api.divar_search_engine, "search", fake_search)

    result = api.get_dynamic_market_data("bosch_gbh_2_26", city="unknown-city")

    assert result is None
    assert calls == [], calls


def test_known_city_is_passed_to_market_search(monkeypatch):
    from backend import api

    calls = []

    def fake_search(city, query, variant=None):
        calls.append(city)
        return {"results": []}

    monkeypatch.setattr(api.divar_search_engine, "search", fake_search)

    result = api.get_dynamic_market_data("bosch_gbh_2_26", city="karaj")

    assert result is None
    assert calls == ["karaj"], calls
