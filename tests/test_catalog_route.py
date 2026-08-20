from backend.web_app import app


def test_catalog_route_returns_canonical_tools():
    client = app.test_client()
    response = client.get("/catalog")
    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload["tools"]) == 8
    assert payload["tools"][0]["id"] == "bosch_gbh_2_26"


def test_catalog_route_is_read_only():
    client = app.test_client()
    response = client.post("/catalog")
    assert response.status_code == 405
