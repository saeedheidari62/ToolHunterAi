from backend.notification_ledger import NotificationLedger


def test_notification_ledger_survives_reopen(tmp_path):
    path = tmp_path / "delivery.sqlite3"
    first = NotificationLedger(path)
    assert first.was_sent("event-1") is False
    first.mark_sent("event-1")

    second = NotificationLedger(path)
    assert second.was_sent("event-1") is True
    assert second.was_sent("event-2") is False
