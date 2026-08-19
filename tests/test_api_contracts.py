from backend import api


def test_dynamic_market_rejects_unknown_city():
    assert api.get_dynamic_market_data("makita_hr2470", city="unknown-city") is None


def test_analyze_endpoint_rejects_missing_ads_field():
    client = api.app.test_client()
    response = client.post("/analyze", json={})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Field 'ads' is required."


def test_analyze_endpoint_rejects_non_list_ads():
    client = api.app.test_client()
    response = client.post("/analyze", json={"ads": {}})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Field 'ads' must be a list."


def test_analyze_endpoint_rejects_empty_ads():
    client = api.app.test_client()
    response = client.post("/analyze", json={"ads": []})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Ads list cannot be empty."
