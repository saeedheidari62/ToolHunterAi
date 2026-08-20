from backend.auto_scanner import AutoScanner


def test_multi_city_scan_preserves_healthy_opportunities_after_partial_failures():
    class FakeDiscovery:
        def discover(self, city, query, limit):
            if city == "karaj":
                raise RuntimeError("marketplace timeout")
            return {
                "searched": 2,
                "filtered": 1,
                "selected": 1,
                "analyzed": 1,
                "search_batches": 1,
                "ranking": [{
                    "url": f"https://divar.ir/v/{city}",
                    "decision": "BUY",
                    "buy_score": 90,
                    "risk_score": 25,
                    "ad_score": 90,
                }],
            }

    class FakeScanner(AutoScanner):
        def load_catalog(self):
            return [{"id": "bosch_gbh_2_26", "name": "Bosch GBH 2-26"}]

    result = FakeScanner(discovery_service=FakeDiscovery()).scan_cities(
        ["tehran", "karaj", "mashhad"],
        top_n=5,
    )

    assert result["cities_scanned"] == 3
    assert result["candidate_pool"] == 2
    assert result["scan_health"]["status"] == "DEGRADED"
    assert result["scan_health"]["failed_tool_runs"] == 1
    assert len(result["ranking"]) == 2
    assert result["best_choice"]["city"] in {"tehran", "mashhad"}
