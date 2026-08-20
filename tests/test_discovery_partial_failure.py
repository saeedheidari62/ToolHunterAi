from backend.discovery_service import DiscoveryService


def test_discover_keeps_healthy_results_when_one_analysis_fails(monkeypatch):
    service = DiscoveryService()

    class FakeSearch:
        def search(self, city, query, variant=None):
            return {
                "results": [
                    {"url": "https://divar.ir/v/1", "title": "Makita HR2470", "price": 7000000},
                    {"url": "https://divar.ir/v/2", "title": "Makita HR2470", "price": 7500000},
                    {"url": "https://divar.ir/v/3", "title": "Makita HR2470", "price": 8000000},
                ]
            }

        def filter_results(self, results, query, variant=None):
            return results

    monkeypatch.setattr("backend.discovery_service.divar_search_engine", FakeSearch())

    def fake_analyze(ad):
        if ad["url"].endswith("/2"):
            raise RuntimeError("fetch failed")
        return {"decision": "BUY", "url": ad["url"], "buy_score": 90}

    monkeypatch.setattr("backend.discovery_service.analyze_single_ad", fake_analyze)
    monkeypatch.setattr(
        "backend.discovery_service.ranker",
        type("FakeRanker", (), {"rank": lambda self, results: {
            "total_ads": len(results),
            "best_choice": results[0],
            "ranking": results,
        }})(),
    )

    result = service.discover("tehran", "makita_hr2470", limit=3)

    assert result["selected"] == 3
    assert result["analyzed"] == 2
    assert len(result["errors"]) == 1
    assert result["errors"][0]["url"] == "https://divar.ir/v/2"
    assert result["best_choice"]["url"] == "https://divar.ir/v/1"
    assert [item["url"] for item in result["ranking"]] == [
        "https://divar.ir/v/1",
        "https://divar.ir/v/3",
    ]
