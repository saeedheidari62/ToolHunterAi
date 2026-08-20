from backend.auto_scanner import AutoScanner


class FakeDiscovery:
    def __init__(self):
        self.calls = []

    def discover(self, city, query, limit):
        self.calls.append((city, query, limit))
        return {
            "searched": 10,
            "filtered": 4,
            "selected": 2,
            "analyzed": 2,
            "search_batches": 3,
            "best_choice": {"decision": "BUY", "buy_score": 90, "risk_score": 20},
            "ranking": [
                {"token": "shared", "decision": "BUY", "buy_score": 90, "risk_score": 20, "ad_score": 90, "price_difference_percent": -20},
                {"token": "unique-" + city, "decision": "REVIEW", "buy_score": 70, "risk_score": 40, "ad_score": 70, "price_difference_percent": -5},
            ],
        }


def test_scanner_loads_catalog_and_scans_each_tool():
    fake = FakeDiscovery()
    scanner = AutoScanner(discovery_service=fake)
    result = scanner.scan("tehran")
    assert result["tools_scanned"] == 8
    assert result["cities_scanned"] == 1
    assert result["opportunities"] == 9
    assert len(fake.calls) == 8


def test_scanner_multi_city_deduplicates_and_globally_ranks():
    fake = FakeDiscovery()
    scanner = AutoScanner(discovery_service=fake)
    result = scanner.scan_cities(["tehran", "karaj"])
    assert result["cities_scanned"] == 2
    assert result["tools_scanned"] == 8
    assert result["candidate_pool"] == 32
    assert result["opportunities"] == 17
    assert result["duplicates_removed"] == 15
    assert result["best_choice"]["opportunity_score"] >= 60
    assert {item["city"] for item in result["ranking"]} == {"tehran", "karaj"}


def test_scanner_rejects_missing_city():
    result = AutoScanner(discovery_service=FakeDiscovery()).scan("")
    assert result["error"] == "INVALID_SCAN_INPUT"
