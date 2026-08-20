from backend.telegram_notification import TelegramNotificationProvider


def test_telegram_provider_requires_configuration():
    provider = TelegramNotificationProvider()
    try:
        provider.send({"label": "BUY", "tool_id": "bosch"})
    except ValueError as exc:
        assert "configuration" in str(exc)
    else:
        raise AssertionError("missing Telegram configuration must fail safely")


def test_telegram_provider_formats_alert():
    provider = TelegramNotificationProvider("token", "chat")
    text = provider._format({"label": "BUY", "title": "Bosch GBH 2-26", "price": 8500000, "url": "https://example.com"})
    assert "BUY" in text
    assert "Bosch GBH 2-26" in text
    assert "8500000" in text
    assert "https://example.com" in text
