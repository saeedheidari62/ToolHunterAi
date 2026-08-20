from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class NotificationResult:
    status: str
    delivered: int = 0
    error: str | None = None


class NotificationProvider(Protocol):
    def send(self, alert: dict[str, Any]) -> None: ...


class ConsoleNotificationProvider:
    def __init__(self):
        self.sent: list[dict[str, Any]] = []

    def send(self, alert: dict[str, Any]) -> None:
        self.sent.append(dict(alert))


class NotificationService:
    def __init__(self, provider: NotificationProvider):
        self.provider = provider

    def send(self, alerts: list[dict[str, Any]]) -> NotificationResult:
        delivered = 0
        try:
            for alert in alerts:
                self.provider.send(alert)
                delivered += 1
        except Exception as exc:
            return NotificationResult("ERROR", delivered, type(exc).__name__)
        return NotificationResult("COMPLETED", delivered)
