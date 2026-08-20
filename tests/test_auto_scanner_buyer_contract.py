from backend.auto_scanner import AutoScanner


class FakeDiscovery:
    def discover(self, city, query, limit=5):
        return {
            "searched": 1,
            "filtered": 1,
            "selected": 1,
            "analyzed": 1,
            "ranking": [{
                "url": f"https://divar.ir/v/{city}-{query}",
                "title": f"{query} listing",
                "tool": query,
                "decision": "BUY",
                "buy_score": 90,
                "risk_score": 30,
                "ad_score": 90,
                "price_difference_percent": -18,
                "has_test": True,
                "has_warranty": False,
                "opportunity_score": 82,
            }],
            "best_choice": None,
        }


def test_scanner_exposes_safe_buyer_opportunity_contract():
    scanner = AutoScanner(discovery_service=FakeDiscovery())
    result = scanner.scan_cities(["tehran"], tool_ids=["bosch_gbh_2_26"])

    assert result["scan_health"]["status"] == "HEALTHY"
    assert len(result["buyer_opportunities"]) == 1
    opportunity = result["buyer_opportunities"][0]
    assert opportunity["status"] == "BUY_NOW"
    assert opportunity["url"].startswith("https://divar.ir/v/")
    assert opportunity["evidence"]
