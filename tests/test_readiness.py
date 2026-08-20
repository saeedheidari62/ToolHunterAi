from backend.readiness import readiness
from backend.web_app import app


def test_readiness_defaults_to_safe_not_ready_when_worker_disabled():
    payload = readiness(type("Config", (), {"worker_enabled": False, "notification_enabled": False, "validate": lambda self: {"ok": True}})())
    assert payload["ready"] is True
    assert payload["config_valid"] is True


def test_readiness_rejects_invalid_notification_configuration():
    config = type("Config", (), {"worker_enabled": True, "notification_enabled": True, "validate": lambda self: {"ok": False, "error": "incomplete"}})()
    payload = readiness(config)
    assert payload["ready"] is False
    assert payload["error"] == "incomplete"


def test_readiness_endpoint_contract():
    client = app.test_client()
    response = client.get("/readiness")
    assert response.status_code in (200, 503)
    payload = response.get_json()
    assert isinstance(payload["ready"], bool)
    assert isinstance(payload["config_valid"], bool)
    assert isinstance(payload["worker_enabled"], bool)
    assert isinstance(payload["notification_enabled"], bool)
