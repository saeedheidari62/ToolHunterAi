from backend.auto_scanner import AutoScanner


def test_scan_health_reports_degraded_partial_failure():
    class FakeDiscovery:
        def discover(self, city, query, limit):
            if city == "karaj":
                raise RuntimeError("temporary failure")
            return {"ranking": [{"url": f"https://divar.ir/v/{city}", "buy_score": 90, "risk_score": 20}]}

    class FakeScanner(AutoScanner):
        def load_catalog(self):
            return [{"id": "bosch_gbh_2_26", "name": "Bosch GBH 2-26"}]

    result = FakeScanner(discovery_service=FakeDiscovery()).scan_cities(["tehran", "karaj"])

    assert result["scan_health"] == {
        "status": "DEGRADED",
        "attempted_tool_runs": 2,
        "failed_tool_runs": 1,
        "successful_tool_runs": 1,
    }
