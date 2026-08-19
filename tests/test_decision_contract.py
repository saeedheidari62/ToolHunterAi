from backend.decision_engine import make_decision


def test_decision_result_always_exposes_market_contract(monkeypatch):
    from backend import decision_engine

    monkeypatch.setattr(
        decision_engine,
        "load_tool",
        lambda _: {"risk": {"score": 10}, "buy_score": 90, "market": {"used_price_min": 100, "used_price_max": 200}},
    )
    monkeypatch.setattr(decision_engine, "analyze_description", lambda _: {"description_risk": 0, "description_reasons": [], "price_signal": "NONE"})
    monkeypatch.setattr(decision_engine.ImageDownloader, "download", lambda self, _: [])
    monkeypatch.setattr(decision_engine, "analyze_image", lambda _: {"image_risk": 0, "image_reasons": []})
    monkeypatch.setattr(decision_engine, "analyze_price", lambda *_args, **_kwargs: {
        "price_status": "GOOD_PRICE",
        "price_score": 90,
        "price_difference_percent": -10.0,
        "price_reason": [],
        "market_source": "dynamic",
    })

    result = make_decision({
        "tool_name": "bosch_gbh_2_26",
        "asking_price": 150,
        "has_test": True,
        "has_warranty": False,
        "description": "",
        "ad_score": 90,
        "analysis": [],
    })

    assert result["market_source"] == "dynamic"
    assert "market_confidence" in result
    assert "price_status" in result
    assert "price_difference_percent" in result
    assert result["decision"] in {"BUY", "REVIEW", "DON'T BUY"}
