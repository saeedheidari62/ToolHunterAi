from backend.monitoring_controller import MonitoringController
from backend.watchlist_store import WatchlistStore


class FakeScanner:
    def __init__(self):
        self.calls = []

    def scan_cities(self, cities, tool_ids=None, top_n=None):
        self.calls.append((cities, tool_ids, top_n))
        return {"cities": cities, "tool_ids": tool_ids, "top_n": top_n, "ok": True}


def test_monitoring_controller_restores_watchlist_and_runs(tmp_path):
    store = WatchlistStore(tmp_path / "monitor.sqlite3")
    store.upsert("bosch", ["tehran", "karaj"], interval_seconds=3600, tool_ids=["bosch_gbh_2_26"], top_n=3)

    scanner = FakeScanner()
    controller = MonitoringController(scanner, watchlist_store=store)
    result = controller.run_now("bosch")

    assert result["status"] == "COMPLETED"
    assert scanner.calls == [(["tehran", "karaj"], ["bosch_gbh_2_26"], 3)]


def test_monitoring_controller_disable_removes_job(tmp_path):
    store = WatchlistStore(tmp_path / "monitor.sqlite3")
    scanner = FakeScanner()
    controller = MonitoringController(scanner, watchlist_store=store)
    controller.upsert_watch("bosch", ["tehran"], interval_seconds=3600)
    assert controller.status()["active_jobs"] == 0
    assert controller.remove_watch("bosch") is True
    assert store.get("bosch")["enabled"] is False
