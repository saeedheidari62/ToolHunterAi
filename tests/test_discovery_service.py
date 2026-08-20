from backend.discovery_service import DiscoveryService


def test_discover_rejects_missing_search_input():
    result = DiscoveryService().discover("", "makita_hr2470")
    assert result["error"] == "INVALID_SEARCH_INPUT"


def test_discover_caps_limit_to_five(monkeypatch):
    service = DiscoveryService()

    class FakeSearch:
        def search(self, city, query, variant=None):
            return {
                "results": [
                    {"url": f"https://divar.ir/v/{index}", "title": "tool", "price": 1}
                    for index in range(10)
                ]
            }

        def filter_results(self, results, query, variant=None):
            return results

    monkeypatch.setattr("backend.discovery_service.divar_search_engine", FakeSearch())
    monkeypatch.setattr(
        "backend.discovery_service.analyze_single_ad",
        lambda ad: {"decision": "BUY", "url": ad["url"], "buy_score": 90},
    )

    result = service.discover("tehran", "makita_hr2470", limit=50)
    assert result["selected"] == 5
    assert result["analyzed"] == 5
