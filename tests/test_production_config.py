from backend.production_config import ProductionConfig


def test_production_config_defaults_are_safe():
    config = ProductionConfig({})
    assert config.notification_enabled is False
    assert config.worker_enabled is False
    assert config.validate() == {"ok": True}


def test_enabled_notifications_require_complete_telegram_config():
    config = ProductionConfig({"NOTIFICATION_ENABLED": "true", "TELEGRAM_BOT_TOKEN": "token"})
    result = config.validate()
    assert result["ok"] is False
    assert "incomplete" in result["error"]


def test_complete_telegram_config_validates():
    config = ProductionConfig({"NOTIFICATION_ENABLED": "true", "TELEGRAM_BOT_TOKEN": "token", "TELEGRAM_CHAT_ID": "chat", "WORKER_ENABLED": "true"})
    assert config.notification_enabled is True
    assert config.worker_enabled is True
    assert config.validate() == {"ok": True}
