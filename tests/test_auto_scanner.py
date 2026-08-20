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
                {"decision": "BUY", "buy_score": 90, "risk_score": 20, "final_score": 89},
                {"decision": "REVIEW", "buy_score": 70, "risk_score": 40, "final_score": 62},
            ],
        }


def test_scanner_loads_catalog_and_scans_each_tool():
    fake = FakeDiscovery()
    scanner = AutoScanner(discovery_service=fake)

    result = scanner.scan("tehran")

    assert result["tools_scanned"] == 8
    assert result["tools_completed"] == 8
    assert result["opportunities"] == 16
    assert len(fake.calls) == 8
    assert all(call[0] == "tehran" and call[2] == 5 for call in fake.calls)
    assert result["best_choice"]["decision"] == "BUY"


def test_scanner_rejects_missing_city():
    result = AutoScanner(discovery_service=FakeDiscovery()).scan("")

    assert result["error"] == "INVALID_SCAN_INPUT"
