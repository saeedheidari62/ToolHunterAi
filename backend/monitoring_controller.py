from .monitoring_metrics import MonitoringMetrics
from .scan_scheduler import ScanScheduler
from .watchlist_store import WatchlistStore


class MonitoringController:
    """Bridge persistent watchlists to the bounded automated scanner."""

    def __init__(self, scanner, watchlist_store=None, scheduler=None, metrics=None):
        self.scanner = scanner
        self.watchlist_store = watchlist_store or WatchlistStore()
        self.metrics = metrics or MonitoringMetrics()
        self.scheduler = scheduler or ScanScheduler(self._run_watchlist)
        self._sync_watchlists()

    def _sync_watchlists(self):
        for watch in self.watchlist_store.list_enabled():
            self.scheduler.add_job(
                watch["watch_id"], watch["cities"],
                interval_seconds=watch["interval_seconds"],
                tool_ids=watch["tool_ids"], top_n=watch["top_n"],
            )

    def _run_watchlist(self, cities, tool_ids=None, top_n=None):
        result = self.scanner.scan_cities(cities, tool_ids=tool_ids, top_n=top_n)
        if isinstance(result, dict):
            opportunities = result.get("opportunities")
            if isinstance(opportunities, list):
                for _ in opportunities:
                    self.metrics.record("OPPORTUNITY")
            elif isinstance(opportunities, int):
                for _ in range(max(opportunities, 0)):
                    self.metrics.record("OPPORTUNITY")
        return result

    def upsert_watch(self, watch_id, cities, interval_seconds=3600, tool_ids=None, top_n=None, enabled=True):
        self.watchlist_store.upsert(watch_id, cities, interval_seconds, tool_ids, top_n, enabled)
        self.scheduler.remove_job(watch_id)
        if enabled:
            self.scheduler.add_job(watch_id, cities, interval_seconds, tool_ids, top_n)
        return self.watchlist_store.get(watch_id)

    def remove_watch(self, watch_id):
        removed = self.scheduler.remove_job(watch_id)
        self.watchlist_store.upsert(watch_id, [], 3600, enabled=False)
        return removed

    def run_due(self):
        results = self.scheduler.run_due()
        for result in results:
            self._record_run(result)
        return results

    def run_now(self, watch_id):
        result = self.scheduler.run_job(watch_id, force=True)
        self._record_run(result)
        return result

    def _record_run(self, result):
        status = result.get("status")
        if status in {"COMPLETED", "ERROR", "SKIPPED"}:
            self.metrics.record(status, job_id=result.get("job_id"), reason=result.get("reason"), error=result.get("error"))

    def record_notification(self, sent=True, **data):
        self.metrics.record("NOTIFICATION_SENT" if sent else "NOTIFICATION_FAILED", **data)

    def status(self):
        payload = self.scheduler.status()
        payload["metrics"] = self.metrics.snapshot()
        return payload
