from backend.web_app import app


def test_web_health_endpoint_release_contract():
    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["service"] == "ToolHunterAI Web"
    assert payload["status"] == "ok"
    assert isinstance(payload["ai_discovery_enabled"], bool)
