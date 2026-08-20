from backend.discovery_service import DiscoveryService
from backend.divar_search_engine import DivarSearchEngine


def test_search_batches_runs_distinct_alias_queries(monkeypatch):
    engine = DivarSearchEngine()
    calls = []

    def fake_search_query(city, query):
        calls.append((city, query))
        return {
            "results": [
                {
                    "token": query,
                    "url": f"https://divar.ir/v/{len(calls)}",
                    "title": query,
                    "price": 1000000,
                }
            ],
            "search_url": f"https://divar.ir/s/{city}?q={query}",
        }

    monkeypatch.setattr(engine, "_search_query", fake_search_query)

    result = engine.search_batches("tehran", "makita_hr2470", max_batches=3)

    assert result["batch_count"] == 3
    assert len(calls) == 3
    assert len({query for _, query in calls}) == 3
    assert len(result["results"]) == 3


def test_discovery_uses_multi_batch_search_when_available(monkeypatch):
    service = DiscoveryService()
    analyzed = []

    class FakeSearch:
        def search_batches(self, city, query, variant=None, max_batches=None):
            assert city == "tehran"
            assert query == "makita_hr2470"
            assert max_batches == 5
            return {
                "results": [
                    {"token": "a", "url": "https://divar.ir/v/a", "title": "Makita HR2470", "price": 7000000},
                    {"token": "a", "url": "https://divar.ir/v/a-copy", "title": "Makita HR2470", "price": 7000000},
                    {"token": "b", "url": "https://divar.ir/v/b", "title": "HR2470", "price": 7500000},
                ],
                "batch_count": 2,
                "errors": [],
            }

        def filter_results(self, results, query, variant=None):
            return results

    monkeypatch.setattr("backend.discovery_service.divar_search_engine", FakeSearch())

    def fake_analyze(ad):
        analyzed.append(ad["url"])
        return {"decision": "BUY", "url": ad["url"], "buy_score": 90}

    monkeypatch.setattr("backend.discovery_service.analyze_single_ad", fake_analyze)

    result = service.discover("tehran", "makita_hr2470", limit=5)

    assert result["search_batches"] == 2
    assert result["searched"] == 2
    assert result["selected"] == 2
    assert result["analyzed"] == 2
    assert analyzed == [
        "https://divar.ir/v/a",
        "https://divar.ir/v/b",
    ]
