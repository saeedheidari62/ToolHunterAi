from datetime import datetime, timezone

from backend.scan_scheduler import ScanScheduler
from backend.watchlist_store import WatchlistStore


def test_scheduler_runs_due_job_and_schedules_next_run():
    calls = []
    now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]

    def runner(cities, tool_ids=None, top_n=None):
        calls.append((cities, tool_ids, top_n))
        return {"buyer_best_choice": "deal-1"}

    scheduler = ScanScheduler(runner, now=lambda: now[0])
    scheduler.add_job("daily", ["tehran"], interval_seconds=60, tool_ids=["bosch"], top_n=5)
    result = scheduler.run_due()

    assert result[0]["status"] == "COMPLETED"
    assert calls == [(["tehran"], ["bosch"], 5)]
    assert scheduler.status()["jobs"][0]["status"] == "READY"


def test_scheduler_skips_not_due_job():
    scheduler = ScanScheduler(lambda *args, **kwargs: {})
    scheduler.add_job("later", ["tehran"], interval_seconds=60)
    scheduler.run_job("later", force=True)
    result = scheduler.run_job("later")
    assert result["status"] == "SKIPPED"
    assert result["reason"] == "NOT_DUE"


def test_watchlist_persists_across_store_instances(tmp_path):
    db = tmp_path / "watch.sqlite3"
    first = WatchlistStore(db)
    first.upsert("w1", ["tehran", "karaj"], interval_seconds=300, tool_ids=["bosch"], top_n=3)

    second = WatchlistStore(db)
    item = second.get("w1")
    assert item["cities"] == ["tehran", "karaj"]
    assert item["tool_ids"] == ["bosch"]
    assert item["interval_seconds"] == 300
    assert item["top_n"] == 3
    assert second.list_enabled()[0]["watch_id"] == "w1"
