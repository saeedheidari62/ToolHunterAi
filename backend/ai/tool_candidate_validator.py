class ToolCandidateValidator:
    """Validate discovered tool candidates before any Knowledge Base promotion."""

    CITY_ALIASES = {
        "تهران": "tehran",
        "tehran": "tehran",
        "کرج": "karaj",
        "karaj": "karaj",
        "مشهد": "mashhad",
        "mashhad": "mashhad",
        "اصفهان": "isfahan",
        "isfahan": "isfahan",
        "شیراز": "shiraz",
        "shiraz": "shiraz",
        "تبریز": "tabriz",
        "tabriz": "tabriz",
    }

    def __init__(self, search_engine, min_samples=2):
        self.search_engine = search_engine
        self.min_samples = int(min_samples)

    def _normalize_city(self, city):
        value = str(city or "").strip().lower()
        return self.CITY_ALIASES.get(value)

    def validate(self, candidate, city=None):
        if not isinstance(candidate, dict):
            return None

        brand = str(candidate.get("brand", "")).strip()
        model = str(candidate.get("model", "")).strip()
        confidence = candidate.get("confidence", 0)
        variant = str(candidate.get("variant", "")).strip()

        if not brand or not model:
            return {"status": "REJECTED", "reason": "Brand and model are required."}

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0

        if confidence < 0.80:
            return {"status": "REJECTED", "reason": "Discovery confidence is below validation threshold."}

        city_slug = self._normalize_city(city)
        if not city_slug:
            return {
                "status": "UNVERIFIED",
                "brand": brand,
                "model": model,
                "variant": variant,
                "confidence": confidence,
                "evidence": candidate.get("evidence", []),
                "technical_data": candidate.get("technical_data", candidate.get("technical", {})),
                "technical_sources": candidate.get("technical_sources", []),
                "market_sample_count": 0,
                "market_data": None,
                "reason": "A supported marketplace city is required for market validation.",
            }

        query = f"{brand} {model}"
        try:
            search_result = self.search_engine.search(city_slug, query, variant=variant or None)
            results = search_result.get("results", [])
        except TypeError:
            try:
                search_result = self.search_engine.search(city_slug, query)
                results = search_result.get("results", [])
            except Exception:
                results = None
        except Exception:
            results = None

        if results is None:
            return {
                "status": "UNVERIFIED",
                "brand": brand,
                "model": model,
                "variant": variant,
                "confidence": confidence,
                "evidence": candidate.get("evidence", []),
                "technical_data": candidate.get("technical_data", candidate.get("technical", {})),
                "technical_sources": candidate.get("technical_sources", []),
                "market_sample_count": 0,
                "market_data": None,
                "reason": "Market validation search failed.",
            }

        model_key = "".join(ch.lower() for ch in model if ch.isalnum())
        matched = []
        for item in results:
            title = str(item.get("title", ""))
            title_key = "".join(ch.lower() for ch in title if ch.isalnum())
            if model_key and model_key in title_key and item.get("price") is not None:
                matched.append(item)

        market_data = None
        effective_sample_count = 0
        if matched:
            try:
                market_result = self.search_engine.get_market_prices({"results": matched})
                if isinstance(market_result, dict) and market_result.get("valid"):
                    effective_sample_count = int(market_result.get("sample_count", len(matched)))
                    market_data = {
                        "used_price_min": market_result.get("min_price"),
                        "used_price_max": market_result.get("max_price"),
                        "median_price": market_result.get("median_price"),
                        "sample_count": effective_sample_count,
                        "price_confidence": "HIGH" if effective_sample_count >= 3 else "MEDIUM" if effective_sample_count >= 2 else "LOW",
                        "sources": ["divar"],
                        "city": city_slug,
                    }
            except Exception:
                market_data = None
                effective_sample_count = 0

        status = "VALIDATED" if effective_sample_count >= self.min_samples else "UNVERIFIED"

        return {
            "status": status,
            "brand": brand,
            "model": model,
            "variant": variant,
            "confidence": confidence,
            "evidence": candidate.get("evidence", []),
            "technical_data": candidate.get("technical_data", candidate.get("technical", {})),
            "technical_sources": candidate.get("technical_sources", []),
            "market_sample_count": effective_sample_count,
            "market_data": market_data,
            "query": query,
            "city": city_slug,
            "reason": "Candidate model was found in multiple marketplace listings." if status == "VALIDATED" else "Insufficient marketplace evidence to validate the candidate.",
        }
