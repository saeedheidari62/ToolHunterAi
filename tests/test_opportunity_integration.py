from backend import api


def test_analyze_single_ad_exposes_opportunity_intelligence(monkeypatch):
    monkeypatch.setattr(api, "prepare_ad", lambda ad: dict(ad))
    monkeypatch.setattr(api.normalizer, "normalize", lambda ad: {"valid": True, "ad": {"title": ad["title"], "description": ad.get("description", ""), "price": ad["price"], "seller_type": "Personal", "testing": True, "warranty": True, "condition": "used"}})
    monkeypatch.setattr(api.collector, "collect", lambda **kwargs: {"title": kwargs["title"], "description": kwargs["description"], "price": kwargs["price"], "seller_type": kwargs["seller_type"], "has_test": True, "has_warranty": True, "brand_model": ""})
    monkeypatch.setattr(api.matcher, "match_all", lambda text: ["bosch_gbh_2_26"])
    monkeypatch.setattr(api.variant_matcher, "detect", lambda text, tool_id: None)
    monkeypatch.setattr(api, "get_dynamic_market_data", lambda *args, **kwargs: {"valid": True, "sample_count": 3, "used_price_min": 9000000, "used_price_max": 10000000})
    monkeypatch.setattr(api, "make_decision", lambda payload: {"decision": "BUY", "buy_score": 95, "risk_score": 20, "price_difference_percent": -15, "price_status": "VERY_GOOD_PRICE"})
    monkeypatch.setattr(api, "analyze_ad", lambda ad: {"ad_score": 90, "analysis": "strong"})

    result = api.analyze_single_ad({"title": "Bosch GBH 2-26", "description": "test warranty", "price": 8000000})

    assert result["decision"] == "BUY"
    assert "opportunity_score" in result
    assert result["opportunity_status"] == "OPPORTUNITY"


def test_analyze_endpoint_returns_opportunity_ranking(monkeypatch):
    monkeypatch.setattr(api, "analyze_single_ad", lambda ad: {"decision": "BUY", "buy_score": 95, "risk_score": 20, "ad_score": 90, "price_difference_percent": -20, "has_test": True, "has_warranty": True, "tool": "bosch_gbh_2_26"})
    client = api.app.test_client()
    response = client.post("/analyze", json={"ads": [{"title": "Bosch", "price": 8000000}]})
    assert response.status_code == 200
    body = response.get_json()
    assert body["best_choice"]["opportunity_score"] >= 60
    assert body["ranking"][0]["opportunity_status"] == "OPPORTUNITY"
