from backend.web_app import app


def test_health_exposes_discovery_and_catalog_metadata():
    client = app.test_client()
    payload = client.get("/health").get_json()
    assert payload["status"] == "ok"
    assert payload["service"] == "ToolHunterAI Web"
    assert payload["ai_discovery_enabled"] is True
    assert payload["api_version"] == "v1"
    assert payload["catalog_size"] == 8
