from .notification import NotificationService
from .notification_ledger import NotificationLedger


class AutonomousDelivery:
    """Deliver newly discovered alerts exactly once using persistent state."""

    def __init__(self, alert_engine, notification_service: NotificationService, ledger=None):
        self.alert_engine = alert_engine
        self.notification_service = notification_service
        self.ledger = ledger or NotificationLedger()

    @staticmethod
    def _event_id(alert):
        return str(alert.get("event_id", alert.get("id", ""))).strip()

    def deliver(self, limit=10, min_priority=70):
        alerts = self.alert_engine.recent(limit=limit, min_priority=min_priority)
        pending = [alert for alert in alerts if self._event_id(alert) and not self.ledger.was_sent(self._event_id(alert))]
        if not pending:
            return {"status": "COMPLETED", "alerts_found": len(alerts), "delivered": 0}
        result = self.notification_service.send(pending)
        if result.status == "COMPLETED":
            for alert in pending:
                self.ledger.mark_sent(self._event_id(alert))
        return {"status": result.status, "alerts_found": len(alerts), "delivered": result.delivered, "error": result.error}
