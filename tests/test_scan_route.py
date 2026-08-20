from backend.web_app import app


def test_scan_route_exposes_automated_multi_tool_scanner(monkeypatch):
    class FakeScanner:
        def scan(self, city, limit_per_tool):
            assert city == "tehran"
            assert int(limit_per_tool) == 5
            return {
                "city": city,
                "tools_scanned": 8,
                "tools_completed": 8,
                "opportunities": 1,
                "best_choice": {"tool_id": "bosch_gbh_2_26", "decision": "BUY"},
                "ranking": [{"tool_id": "bosch_gbh_2_26", "decision": "BUY"}],
                "errors": [],
            }

        def scan_cities(self, cities, limit_per_tool, top_n, tool_ids):
            assert cities == ["tehran"]
            assert int(limit_per_tool) == 5
            return self.scan("tehran", limit_per_tool)

    monkeypatch.setattr("backend.web_app.auto_scanner", FakeScanner())
    client = app.test_client()
    response = client.post("/scan", json={"city": "tehran"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["tools_scanned"] == 8
    assert payload["best_choice"]["tool_id"] == "bosch_gbh_2_26"
