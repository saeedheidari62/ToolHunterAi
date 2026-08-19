from backend.decision_engine import make_decision


def _patch_decision(monkeypatch, buy_score=80):
    from backend import decision_engine
    monkeypatch.setattr(decision_engine, "load_tool", lambda _: {"risk": {"score": 0}, "buy_score": buy_score, "market": {"used_price_min": 100, "used_price_max": 200}})
    monkeypatch.setattr(decision_engine, "analyze_description", lambda _: {"description_risk": 0, "description_reasons": [], "price_signal": "NONE"})
    monkeypatch.setattr(decision_engine.ImageDownloader, "download", lambda self, _: [])
    monkeypatch.setattr(decision_engine, "analyze_image", lambda _: {"image_risk": 0, "image_reasons": []})


def test_decision_result_always_exposes_market_contract(monkeypatch):
    from backend import decision_engine
    _patch_decision(monkeypatch, buy_score=90)
    monkeypatch.setattr(decision_engine, "analyze_price", lambda *_args, **_kwargs: {
        "price_status": "GOOD_PRICE", "price_score": 90, "price_difference_percent": -10.0,
        "price_reason": [], "market_source": "dynamic",
    })
    result = make_decision({"tool_name": "bosch_gbh_2_26", "asking_price": 150, "has_test": True, "has_warranty": False, "description": "", "ad_score": 90, "analysis": []})
    assert result["market_source"] == "dynamic"
    assert "market_confidence" in result
    assert "price_status" in result
    assert "price_difference_percent" in result
    assert result["decision"] in {"BUY", "REVIEW", "DON'T BUY"}


def test_numeric_market_confidence_is_normalized(monkeypatch):
    from backend import decision_engine
    _patch_decision(monkeypatch)
    monkeypatch.setattr(decision_engine, "analyze_price", lambda *_args, **_kwargs: {
        "price_status": "FAIR_PRICE", "price_score": 50, "price_difference_percent": 0,
        "price_reason": [], "market_source": "dynamic",
    })
    result = make_decision({"tool_name": "bosch_gbh_2_26", "asking_price": 100, "has_test": True, "has_warranty": False, "description": "", "ad_score": 50, "analysis": [], "market_data": {"confidence": 0.9}})
    assert result["market_confidence"] == "HIGH"
    assert result["market_source"] == "dynamic"


def test_unknown_market_confidence_is_not_trusted(monkeypatch):
    from backend import decision_engine
    _patch_decision(monkeypatch)
    monkeypatch.setattr(decision_engine, "analyze_price", lambda *_args, **_kwargs: {
        "price_status": "FAIR_PRICE", "price_score": 50, "price_difference_percent": 0,
        "price_reason": [], "market_source": "knowledge_base",
    })
    result = make_decision({"tool_name": "bosch_gbh_2_26", "asking_price": 100, "has_test": True, "has_warranty": False, "description": "", "ad_score": 50, "analysis": [], "market_data": {"confidence": "unexpected"}})
    assert result["market_confidence"] is None
