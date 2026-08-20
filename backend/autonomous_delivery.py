from .notification import NotificationService, NotificationResult
from .notification_dedup import NotificationDedupStore


class AutonomousDelivery:
    """Deliver newly discovered alerts exactly once per event id."""

    def __init__(self, alert_engine, notification_service: NotificationService, dedup=None):
        self.alert_engine = alert_engine
        self.notification_service = notification_service
        self.dedup = dedup or NotificationDedupStore()

    def deliver(self, limit=10, min_priority=70):
        alerts = self.alert_engine.recent(limit=limit, min_priority=min_priority)
        pending = self.dedup.filter_unseen(alerts)
        if not pending:
            return {"status": "COMPLETED", "alerts_found": len(alerts), "delivered": 0}
        result = self.notification_service.send(pending)
        if result.status == "COMPLETED":
            for alert in pending:
                self.dedup.mark_sent(str(alert.get("event_id", alert.get("id", ""))))
        return {"status": result.status, "alerts_found": len(alerts), "delivered": result.delivered, "error": result.error}
