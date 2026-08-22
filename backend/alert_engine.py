import os
from datetime import datetime, timedelta, timezone


class AlertEngine:
    """Turn persisted deal events into concise, actionable alerts."""

    MIN_PRIORITY = 70
    DEFAULT_TTL_HOURS = 48

    def __init__(self, ledger, ttl_hours=None):
        self.ledger = ledger
        configured_ttl = ttl_hours if ttl_hours is not None else os.getenv("ALERT_TTL_HOURS", self.DEFAULT_TTL_HOURS)
        try:
            self.ttl_hours = max(1, float(configured_ttl))
        except (TypeError, ValueError):
            self.ttl_hours = self.DEFAULT_TTL_HOURS

    @staticmethod
    def _message(event):
        labels = {
            "DECISION_UPGRADE": "🔥 BUY OPPORTUNITY",
            "PRICE_DROP": "📉 PRICE DROP",
            "NEW_DEAL": "🆕 NEW DEAL",
            "RISK_CHANGE": "⚠️ RISK CHANGE",
            "PRICE_RISE": "📈 PRICE RISE",
            "DECISION_CHANGE": "🔄 DECISION CHANGE",
        }
        return labels.get(event, event)

    def _is_fresh(self, created_at, now=None):
        try:
            timestamp = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            reference = now or datetime.now(timezone.utc)
            return reference - timestamp <= timedelta(hours=self.ttl_hours)
        except (TypeError, ValueError):
            return False

    def recent(self, limit=10, min_priority=MIN_PRIORITY):
        events = self.ledger.recent(limit=100)
        alerts = []
        for event in events:
            if event["priority"] < min_priority or not self._is_fresh(event.get("created_at")):
                continue
            alert = dict(event)
            alert["label"] = self._message(event["event"])
            alerts.append(alert)
            if len(alerts) >= limit:
                break
        return alerts
