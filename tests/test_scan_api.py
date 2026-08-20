from backend.web_app import app


def test_scan_api_accepts_multi_city_and_tool_selection(monkeypatch):
    expected = {
        "cities_scanned": 2,
        "tools_scanned": 2,
        "opportunities": 1,
        "candidate_pool": 2,
        "unique_candidates": 1,
        "duplicates_removed": 1,
        "ranking": [{"city": "tehran", "tool_id": "bosch_gbh_2_26", "opportunity_score": 91}],
        "best_choice": {"city": "tehran", "tool_id": "bosch_gbh_2_26", "opportunity_score": 91},
        "errors": [],
    }
    monkeypatch.setattr(app, "testing", True, raising=False)
    monkeypatch.setattr(
        "backend.web_app.auto_scanner.scan_cities",
        lambda cities, limit_per_tool, top_n, tool_ids: expected,
    )
    client = app.test_client()
    response = client.post("/scan", json={
        "cities": ["tehran", "karaj"],
        "tool_ids": ["bosch_gbh_2_26", "makita_hr2470"],
        "top_n": 10,
    })
    assert response.status_code == 200
    body = response.get_json()
    assert body["cities_scanned"] == 2
    assert body["best_choice"]["opportunity_score"] == 91


def test_scan_api_rejects_missing_cities():
    client = app.test_client()
    response = client.post("/scan", json={"tool_ids": ["bosch_gbh_2_26"]})
    assert response.status_code == 400
    assert response.get_json()["error"] == "INVALID_SCAN_INPUT"
