from backend.autonomous_delivery import AutonomousDelivery
from backend.notification import ConsoleNotificationProvider, NotificationService


class FakeAlerts:
    def __init__(self):
        self.calls = 0
        self.alerts = [{"event_id": "e1", "priority": 90, "label": "🔥 BUY OPPORTUNITY"}]

    def recent(self, limit=10, min_priority=70):
        self.calls += 1
        return self.alerts[:limit]


def test_delivery_sends_new_alert_once():
    provider = ConsoleNotificationProvider()
    service = NotificationService(provider)
    delivery = AutonomousDelivery(FakeAlerts(), service)

    first = delivery.deliver()
    second = delivery.deliver()

    assert first["delivered"] == 1
    assert second["delivered"] == 0
    assert len(provider.sent) == 1


def test_delivery_preserves_provider_failure():
    class FailingProvider:
        def send(self, alert):
            raise RuntimeError("transport down")

    result = AutonomousDelivery(FakeAlerts(), NotificationService(FailingProvider())).deliver()
    assert result["status"] == "ERROR"
    assert result["delivered"] == 0
