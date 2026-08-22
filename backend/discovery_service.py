import re

from .api import analyze_single_ad, divar_search_engine, ranker
from .search_fallback_analyzer import SearchFallbackAnalyzer


class DiscoveryService:
    """Turn a marketplace search into a bounded set of analyzed listings."""

    MAX_LIMIT = 5
    SEARCH_POOL_SIZE = 50
    MAX_SEARCH_BATCHES = 5

    def __init__(self):
        self.search_fallback = SearchFallbackAnalyzer()

    @staticmethod
    def _pre_rank_candidates(candidates, query):
        normalized_query = re.sub(r"\s+", " ", str(query or "").lower().replace("_", " ")).strip()
        query_tokens = [token for token in re.findall(r"[a-z0-9]+", normalized_query) if token]

        def score(item):
            title = str(item.get("title", "")).lower()
            compact_title = re.sub(r"[^a-z0-9آ-ی]+", "", title)
            token_hits = sum(token in title or token in compact_title for token in query_tokens)
            exact_match = 1 if normalized_query and normalized_query in title else 0
            has_price = 1 if item.get("price") not in (None, "", 0) else 0
            return (exact_match, token_hits, has_price)

        return sorted(enumerate(candidates), key=lambda pair: (score(pair[1]), -pair[0]), reverse=True)

    @staticmethod
    def _deduplicate_candidates(candidates):
        seen = set()
        unique = []
        for item in candidates:
            if not isinstance(item, dict):
                continue
            key = item.get("token") or item.get("url")
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    def discover(self, city, query, variant=None, limit=5):
        city = str(city or "").strip()
        query = str(query or "").strip()
        if not city or not query:
            return {"error": "INVALID_SEARCH_INPUT", "message": "city and query are required."}

        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 5
        limit = max(1, min(limit, self.MAX_LIMIT))

        search_batches = getattr(divar_search_engine, "search_batches", None)
        if callable(search_batches):
            search_result = search_batches(city, query, variant=variant, max_batches=self.MAX_SEARCH_BATCHES)
        else:
            search_result = divar_search_engine.search(city, query, variant=variant)

        candidates = search_result.get("results", []) if isinstance(search_result, dict) else []
        candidates = self._deduplicate_candidates(candidates)
        filtered = divar_search_engine.filter_results(candidates, query, variant)
        analysis_pool = filtered[: self.SEARCH_POOL_SIZE]
        ranked_candidates = self._pre_rank_candidates(analysis_pool, query)
        selected_candidates = [item for _, item in ranked_candidates[:limit]]

        results = []
        errors = []
        warnings = []
        for candidate in selected_candidates:
            url = candidate.get("url") if isinstance(candidate, dict) else ""
            if not url:
                errors.append({"url": "", "error": "MISSING_CANDIDATE_URL"})
                continue
            try:
                result = analyze_single_ad({"url": url})
            except Exception as exc:
                errors.append({"url": url, "error": type(exc).__name__})
                continue
            if isinstance(result, dict) and "error" in result:
                error_payload = result
                error_code = str(result.get("error_code") or result.get("error") or "")
                if error_code == "FETCH_INCOMPLETE":
                    tool_id = "bosch_gbh_2_26" if "gbh" in query.lower() else query
                    fallback = self.search_fallback.analyze(candidate, tool_id, city)
                    if fallback:
                        results.append(fallback)
                        warnings.append({"url": url, "type": "FETCH_INCOMPLETE_FALLBACK", "message": fallback["fetch_warning"]})
                        continue
                errors.append({"url": url, "error": error_payload})
            else:
                results.append(result)

        ranking = ranker.rank(results) if results else {"total_ads": 0, "best_choice": None, "ranking": []}
        return {
            "city": city,
            "query": query,
            "variant": variant,
            "searched": len(candidates),
            "filtered": len(filtered),
            "analysis_pool": len(analysis_pool),
            "selected": len(selected_candidates),
            "analyzed": len(results),
            "best_choice": ranking.get("best_choice"),
            "ranking": ranking.get("ranking", []),
            "errors": errors,
            "warnings": warnings,
            "search_error": search_result.get("error") if isinstance(search_result, dict) else "SEARCH_FAILED",
            "search_batches": search_result.get("batch_count", 1) if isinstance(search_result, dict) else 1,
            "search_errors": search_result.get("errors", []) if isinstance(search_result, dict) else [],
        }
