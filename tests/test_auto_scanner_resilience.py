from backend.auto_scanner import AutoScanner


def test_scan_cities_continues_other_cities_after_discovery_failure():
    class FakeDiscovery:
        def discover(self, city, query, limit):
            if city == "karaj":
                raise RuntimeError("temporary discovery failure")
            return {
                "searched": 1,
                "filtered": 1,
                "selected": 1,
                "analyzed": 1,
                "search_batches": 1,
                "best_choice": {"url": f"https://divar.ir/v/{city}", "buy_score": 90, "risk_score": 20},
                "ranking": [{"url": f"https://divar.ir/v/{city}", "buy_score": 90, "risk_score": 20}],
            }

    class FakeCatalogScanner(AutoScanner):
        def load_catalog(self):
            return [{"id": "bosch_gbh_2_26", "name": "Bosch GBH 2-26"}]

    scanner = FakeCatalogScanner(discovery_service=FakeDiscovery())
    result = scanner.scan_cities(["tehran", "karaj", "mashhad"])

    assert result["cities_scanned"] == 3
    assert len(result["city_runs"]) == 3
    assert result["city_runs"][1]["tools_completed"] == 0
    assert len(result["errors"]) == 1
    assert result["errors"][0]["city"] == "karaj"
    assert result["candidate_pool"] == 2
    assert result["unique_candidates"] == 2
