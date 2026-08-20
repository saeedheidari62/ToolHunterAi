from .api import analyze_single_ad, divar_search_engine, ranker


class DiscoveryService:
    """Turn a marketplace search into a bounded set of analyzed listings."""

    MAX_LIMIT = 5
    SEARCH_POOL_SIZE = 20

    def discover(self, city, query, variant=None, limit=5):
        city = str(city or "").strip()
        query = str(query or "").strip()
        if not city or not query:
            return {
                "error": "INVALID_SEARCH_INPUT",
                "message": "city and query are required.",
            }

        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 5
        limit = max(1, min(limit, self.MAX_LIMIT))

        search_result = divar_search_engine.search(city, query, variant=variant)
        candidates = search_result.get("results", []) if isinstance(search_result, dict) else []
        filtered = divar_search_engine.filter_results(candidates, query, variant)

        results = []
        errors = []
        analysis_pool = filtered[: self.SEARCH_POOL_SIZE]
        for candidate in analysis_pool[:limit]:
            url = candidate.get("url") if isinstance(candidate, dict) else ""
            if not url:
                continue
            result = analyze_single_ad({"url": url})
            if isinstance(result, dict) and "error" in result:
                errors.append({"url": url, "error": result})
            else:
                results.append(result)

        ranking = ranker.rank(results) if results else {
            "total_ads": 0,
            "best_choice": None,
            "ranking": [],
        }

        return {
            "city": city,
            "query": query,
            "variant": variant,
            "searched": len(candidates),
            "filtered": len(filtered),
            "analysis_pool": len(analysis_pool),
            "selected": min(len(filtered), limit),
            "analyzed": len(results),
            "best_choice": ranking.get("best_choice"),
            "ranking": ranking.get("ranking", []),
            "errors": errors,
            "search_error": search_result.get("error") if isinstance(search_result, dict) else "SEARCH_FAILED",
        }
