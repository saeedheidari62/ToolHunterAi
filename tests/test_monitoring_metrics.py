from backend.monitoring_controller import MonitoringController
from backend.monitoring_metrics import MonitoringMetrics
from backend.watchlist_store import WatchlistStore


class FakeScanner:
    def scan_cities(self, cities, tool_ids=None, top_n=None):
        return {"opportunities": [{"id": "a"}, {"id": "b"}]}


def test_metrics_track_runs_and_opportunities(tmp_path):
    metrics = MonitoringMetrics()
    controller = MonitoringController(FakeScanner(), WatchlistStore(tmp_path / "m.sqlite3"), metrics=metrics)
    controller.upsert_watch("w", ["tehran"], 3600)
    result = controller.run_now("w")
    assert result["status"] == "COMPLETED"
    snapshot = controller.status()["metrics"]
    assert snapshot["runs_total"] == 1
    assert snapshot["runs_completed"] == 1
    assert snapshot["scan_opportunities"] == 2
    assert snapshot["runs_failed"] == 0


def test_metrics_classify_failures(tmp_path):
    class BrokenScanner:
        def scan_cities(self, *args, **kwargs):
            raise RuntimeError("boom")

    controller = MonitoringController(BrokenScanner(), WatchlistStore(tmp_path / "m.sqlite3"))
    controller.upsert_watch("w", ["tehran"], 3600)
    result = controller.run_now("w")
    assert result["status"] == "ERROR"
    assert controller.status()["metrics"]["runs_failed"] == 1
