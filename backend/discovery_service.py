import re

from .api import analyze_single_ad, divar_search_engine, ranker


class DiscoveryService:
    """Turn a marketplace search into a bounded set of analyzed listings."""

    MAX_LIMIT = 5
    SEARCH_POOL_SIZE = 20

    @staticmethod
    def _pre_rank_candidates(candidates, query):
        """Order candidates by cheap title relevance before expensive analysis."""
        normalized_query = re.sub(r"\s+", " ", str(query or "").lower().replace("_", " ")).strip()
        query_tokens = [token for token in re.findall(r"[a-z0-9]+", normalized_query) if token]

        def score(item):
            title = str(item.get("title", "")).lower()
            compact_title = re.sub(r"[^a-z0-9آ-ی]+", "", title)
            token_hits = sum(token in title or token in compact_title for token in query_tokens)
            exact_match = 1 if normalized_query and normalized_query in title else 0
            has_price = 1 if item.get("price") not in (None, "", 0) else 0
            return (exact_match, token_hits, has_price)

        return sorted(
            enumerate(candidates),
            key=lambda pair: (score(pair[1]), -pair[0]),
            reverse=True,
        )

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

        analysis_pool = filtered[: self.SEARCH_POOL_SIZE]
        ranked_candidates = self._pre_rank_candidates(analysis_pool, query)
        selected_candidates = [item for _, item in ranked_candidates[:limit]]

        results = []
        errors = []
        for candidate in selected_candidates:
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
