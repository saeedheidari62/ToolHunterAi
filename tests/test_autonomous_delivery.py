from backend.autonomous_delivery import AutonomousDelivery
from backend.notification import ConsoleNotificationProvider, NotificationService
from backend.notification_ledger import NotificationLedger


class FakeAlerts:
    def __init__(self):
        self.alerts = [{"event_id": "e1", "priority": 90, "label": "BUY OPPORTUNITY"}]

    def recent(self, limit=10, min_priority=70):
        return self.alerts[:limit]


def test_delivery_uses_persistent_ledger(tmp_path):
    provider = ConsoleNotificationProvider()
    service = NotificationService(provider)
    ledger = NotificationLedger(tmp_path / "delivery.sqlite3")

    first = AutonomousDelivery(FakeAlerts(), service, ledger).deliver()
    second = AutonomousDelivery(FakeAlerts(), service, NotificationLedger(tmp_path / "delivery.sqlite3")).deliver()

    assert first["delivered"] == 1
    assert second["delivered"] == 0
    assert len(provider.sent) == 1


def test_delivery_preserves_provider_failure(tmp_path):
    class FailingProvider:
        def send(self, alert):
            raise RuntimeError("transport down")

    ledger = NotificationLedger(tmp_path / "delivery.sqlite3")
    result = AutonomousDelivery(FakeAlerts(), NotificationService(FailingProvider()), ledger).deliver()
    assert result["status"] == "ERROR"
    assert result["delivered"] == 0
    assert ledger.was_sent("e1") is False
