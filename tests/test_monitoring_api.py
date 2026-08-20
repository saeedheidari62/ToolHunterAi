from backend.web_app import app


def test_monitoring_status_endpoint():
    response = app.test_client().get("/monitoring/status")
    assert response.status_code == 200
    payload = response.get_json()
    assert "active_jobs" in payload


def test_monitoring_watch_and_run_contract(tmp_path, monkeypatch):
    from backend.web_app import monitoring
    from backend.watchlist_store import WatchlistStore

    monkeypatch.setattr(monitoring, "watchlist_store", WatchlistStore(tmp_path / "monitor.sqlite3"))
    monitoring.scheduler.jobs = {}
    monitoring._sync_watchlists()

    response = app.test_client().post("/monitoring/watch", json={"watch_id": "bosch", "cities": ["tehran"], "interval_seconds": 3600, "top_n": 2})
    assert response.status_code == 200
    assert response.get_json()["watch"]["watch_id"] == "bosch"
