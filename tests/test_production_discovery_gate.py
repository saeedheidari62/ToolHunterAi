from backend.web_app import app


def test_production_discovery_gate_contract(monkeypatch):
    class FakeDiscoveryService:
        def discover(self, city, query, variant=None, limit=5):
            return {
                "city": city,
                "query": query,
                "variant": variant,
                "searched": 20,
                "filtered": 8,
                "analysis_pool": 8,
                "selected": 5,
                "analyzed": 5,
                "best_choice": {"url": "https://divar.ir/v/best"},
                "ranking": [
                    {"url": "https://divar.ir/v/best"},
                    {"url": "https://divar.ir/v/2"},
                    {"url": "https://divar.ir/v/3"},
                    {"url": "https://divar.ir/v/4"},
                    {"url": "https://divar.ir/v/5"},
                ],
                "errors": [],
                "search_error": None,
            }

    monkeypatch.setattr("backend.web_app.discovery_service", FakeDiscoveryService())

    client = app.test_client()
    response = client.post(
        "/discover",
        json={"city": "tehran", "query": "makita_hr2470", "limit": 5},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["analysis_pool"] <= 20
    assert data["selected"] <= 5
    assert data["analyzed"] <= 5
    assert data["selected"] == data["analyzed"]
    assert data["ranking"]
    assert data["best_choice"]
    assert data["best_choice"]["url"] == data["ranking"][0]["url"]
