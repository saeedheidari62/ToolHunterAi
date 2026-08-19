from backend.decision_engine import make_decision


def test_low_confidence_market_cannot_produce_buy_decision(monkeypatch):
    monkeypatch.setattr(
        "backend.decision_engine.load_tool",
        lambda _: {
            "risk": {"score": 20},
            "buy_score": 100,
        },
    )
    monkeypatch.setattr(
        "backend.decision_engine.analyze_description",
        lambda _: {"description_risk": 0, "description_reasons": [], "price_signal": "NONE"},
    )
    monkeypatch.setattr(
        "backend.decision_engine.ImageDownloader.download",
        lambda self, _: [],
    )
    monkeypatch.setattr(
        "backend.decision_engine.analyze_image",
        lambda _: {"image_risk": 0, "image_reasons": []},
    )
    monkeypatch.setattr(
        "backend.decision_engine.analyze_price",
        lambda *args, **kwargs: {
            "market_confidence": "LOW",
            "price_status": "LOW_PRICE",
            "price_score": 100,
            "price_difference_percent": -30,
            "market_source": "dynamic",
            "price_reason": [],
        },
    )

    result = make_decision(
        {
            "tool_name": "test_tool",
            "asking_price": 10,
            "market_data": {"valid": True, "confidence": "LOW"},
            "has_test": True,
            "has_warranty": True,
            "description": "",
            "ad_score": 100,
            "analysis": [],
        }
    )

    assert result["market_confidence"] == "LOW"
    assert result["decision"] == "REVIEW"


def test_high_confidence_market_can_reach_buy(monkeypatch):
    monkeypatch.setattr(
        "backend.decision_engine.load_tool",
        lambda _: {
            "risk": {"score": 20},
            "buy_score": 100,
        },
    )
    monkeypatch.setattr(
        "backend.decision_engine.analyze_description",
        lambda _: {"description_risk": 0, "description_reasons": [], "price_signal": "NONE"},
    )
    monkeypatch.setattr(
        "backend.decision_engine.ImageDownloader.download",
        lambda self, _: [],
    )
    monkeypatch.setattr(
        "backend.decision_engine.analyze_image",
        lambda _: {"image_risk": 0, "image_reasons": []},
    )
    monkeypatch.setattr(
        "backend.decision_engine.analyze_price",
        lambda *args, **kwargs: {
            "market_confidence": "HIGH",
            "price_status": "LOW_PRICE",
            "price_score": 100,
            "price_difference_percent": -5,
            "market_source": "dynamic",
            "price_reason": [],
        },
    )

    result = make_decision(
        {
            "tool_name": "test_tool",
            "asking_price": 10,
            "market_data": {"valid": True, "confidence": "HIGH"},
            "has_test": True,
            "has_warranty": True,
            "description": "",
            "ad_score": 100,
            "analysis": [],
        }
    )

    assert result["market_confidence"] == "HIGH"
    assert result["decision"] == "BUY"
