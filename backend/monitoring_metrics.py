from collections import Counter
from threading import Lock


class MonitoringMetrics:
    def __init__(self):
        self._lock = Lock()
        self._counts = Counter()
        self._last = {}

    def record(self, event, **data):
        with self._lock:
            self._counts[event] += 1
            self._last[event] = dict(data)

    def snapshot(self):
        with self._lock:
            return {
                "runs_total": sum(self._counts[event] for event in ("COMPLETED", "ERROR", "SKIPPED")),
                "runs_completed": self._counts["COMPLETED"],
                "runs_failed": self._counts["ERROR"],
                "runs_skipped": self._counts["SKIPPED"],
                "scan_opportunities": self._counts["OPPORTUNITY"],
                "notifications_sent": self._counts["NOTIFICATION_SENT"],
                "notifications_failed": self._counts["NOTIFICATION_FAILED"],
                "last_completed": self._last.get("COMPLETED"),
                "last_error": self._last.get("ERROR"),
            }
