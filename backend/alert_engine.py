class AlertEngine:
    """Turn persisted deal events into concise, actionable alerts."""

    MIN_PRIORITY = 70

    def __init__(self, ledger):
        self.ledger = ledger

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

    def recent(self, limit=10, min_priority=MIN_PRIORITY):
        events = self.ledger.recent(limit=max(limit * 3, 20))
        alerts = []
        for event in events:
            if event["priority"] < min_priority:
                continue
            alert = dict(event)
            alert["label"] = self._message(event["event"])
            alerts.append(alert)
            if len(alerts) >= limit:
                break
        return alerts
