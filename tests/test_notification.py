from backend.notification import ConsoleNotificationProvider, NotificationService
from backend.notification_dedup import NotificationDedupStore


def test_notification_service_delivers_alerts():
    provider = ConsoleNotificationProvider()
    result = NotificationService(provider).send([{"event_id": "e1", "label": "PRICE DROP"}, {"event_id": "e2"}])
    assert result.status == "COMPLETED"
    assert result.delivered == 2
    assert [x["event_id"] for x in provider.sent] == ["e1", "e2"]


def test_notification_service_contains_provider_failure():
    class Broken:
        def send(self, alert):
            raise RuntimeError("down")

    result = NotificationService(Broken()).send([{"event_id": "e1"}])
    assert result.status == "ERROR"
    assert result.delivered == 0
    assert result.error == "RuntimeError"


def test_dedup_prevents_repeat_delivery():
    store = NotificationDedupStore()
    alerts = [{"event_id": "e1"}, {"event_id": "e2"}]
    assert len(store.filter_unseen(alerts)) == 2
    store.mark_sent("e1")
    unseen = store.filter_unseen(alerts)
    assert unseen == [{"event_id": "e2"}]
