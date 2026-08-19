from backend import api


def test_api_error_contract_has_stable_code_and_message():
    result = api._error("TOOL_NOT_RECOGNIZED", title="Example")
    assert result["error"] == "TOOL_NOT_RECOGNIZED"
    assert result["message"] == api.ERROR_CODES["TOOL_NOT_RECOGNIZED"]
    assert result["title"] == "Example"


def test_dynamic_market_rejects_unknown_city_without_search(monkeypatch):
    called = []

    def fake_search(*args, **kwargs):
        called.append((args, kwargs))
        return {"results": []}

    monkeypatch.setattr(api.divar_search_engine, "search", fake_search)
    assert api.get_dynamic_market_data("makita_hr2470", city="unknown-city") is None
    assert called == []


def test_dynamic_market_source_is_explicit(monkeypatch):
    class FakeEngine:
        def search(self, city, tool_name, variant=None):
            return {"results": [{"title": tool_name, "price": 100}]}

        def filter_results(self, results, tool_name, variant=None):
            return results

        def get_market_prices(self, payload):
            return {
                "valid": True,
                "sample_count": 3,
                "min_price": 90,
                "max_price": 110,
                "median_price": 100,
            }

    monkeypatch.setattr(api, "divar_search_engine", FakeEngine())
    result = api.get_dynamic_market_data("bosch_gbh_2_26", city="tehran", variant="standard")
    assert result["source"] == "dynamic_divar"
    assert result["confidence"] == "HIGH"
    assert result["city"] == "tehran"


def test_analyze_endpoint_rejects_missing_ads_field():
    client = api.app.test_client()
    response = client.post("/analyze", json={})
    assert response.status_code == 400
    assert response.get_json()["error"] == "MISSING_ADS"


def test_analyze_endpoint_rejects_non_list_ads():
    client = api.app.test_client()
    response = client.post("/analyze", json={"ads": {}})
    assert response.status_code == 400
    assert response.get_json()["error"] == "INVALID_ADS"


def test_analyze_endpoint_rejects_empty_ads():
    client = api.app.test_client()
    response = client.post("/analyze", json={"ads": []})
    assert response.status_code == 400
    assert response.get_json()["error"] == "EMPTY_ADS"
