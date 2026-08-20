class NotificationDedupStore:
    """In-memory MVP idempotency store; persistence can be added behind this contract."""

    def __init__(self):
        self._sent: set[str] = set()

    def unseen(self, event_id: str) -> bool:
        return event_id not in self._sent

    def mark_sent(self, event_id: str) -> None:
        self._sent.add(event_id)

    def filter_unseen(self, alerts):
        return [alert for alert in alerts if self.unseen(str(alert.get("event_id", alert.get("id", ""))))]
