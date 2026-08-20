from backend.discovery_service import DiscoveryService
from backend.divar_search_engine import DivarSearchEngine


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


def test_discover_ranks_analyzed_candidates(monkeypatch):
    service = DiscoveryService()

    class FakeSearch:
        def search(self, city, query, variant=None):
            return {
                "results": [
                    {"url": "https://divar.ir/v/1", "title": "tool one", "price": 1},
                    {"url": "https://divar.ir/v/2", "title": "tool two", "price": 2},
                ]
            }

        def filter_results(self, results, query, variant=None):
            return results

    class FakeRanker:
        def rank(self, results):
            return {
                "total_ads": len(results),
                "best_choice": results[1],
                "ranking": list(reversed(results)),
            }

    monkeypatch.setattr("backend.discovery_service.divar_search_engine", FakeSearch())
    monkeypatch.setattr(
        "backend.discovery_service.analyze_single_ad",
        lambda ad: {
            "decision": "BUY",
            "url": ad["url"],
            "buy_score": 90,
        },
    )
    monkeypatch.setattr("backend.discovery_service.ranker", FakeRanker())

    result = service.discover("tehran", "makita_hr2470", limit=2)

    assert result["searched"] == 2
    assert result["selected"] == 2
    assert result["analyzed"] == 2
    assert result["best_choice"]["url"] == "https://divar.ir/v/2"
    assert [item["url"] for item in result["ranking"]] == [
        "https://divar.ir/v/2",
        "https://divar.ir/v/1",
    ]


def test_filter_results_accepts_persian_model_alias_and_rejects_unrelated_listing():
    engine = DivarSearchEngine()
    results = [
        {
            "title": "دریل بتن کن بوش مدل GBH 2-26 چهار حالته",
            "price": 8500000,
            "url": "https://divar.ir/v/gbh226",
        },
        {
            "title": "دریل بتن کن ماکیتا HR2470 سالم",
            "price": 7000000,
            "url": "https://divar.ir/v/hr2470",
        },
        {
            "title": "کیف ابزار بوش GBH 2-26",
            "price": 500000,
            "url": "https://divar.ir/v/bag",
        },
    ]

    filtered = engine.filter_results(results, "bosch_gbh_2_26")

    assert [item["url"] for item in filtered] == ["https://divar.ir/v/gbh226"]
