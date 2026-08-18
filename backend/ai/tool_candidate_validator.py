class ToolCandidateValidator:
    """Validate discovered tool candidates before any Knowledge Base promotion."""

    def __init__(self, search_engine, min_samples=2):
        self.search_engine = search_engine
        self.min_samples = int(min_samples)

    def validate(self, candidate, city="tehran"):
        if not isinstance(candidate, dict):
            return None

        brand = str(candidate.get("brand", "")).strip()
        model = str(candidate.get("model", "")).strip()
        confidence = candidate.get("confidence", 0)

        if not brand or not model:
            return {
                "status": "REJECTED",
                "reason": "Brand and model are required."
            }

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0

        if confidence < 0.80:
            return {
                "status": "REJECTED",
                "reason": "Discovery confidence is below validation threshold."
            }

        query = f"{brand} {model}"
        try:
            search_result = self.search_engine.search(city, query)
            results = search_result.get("results", [])
        except Exception:
            return {
                "status": "UNVERIFIED",
                "brand": brand,
                "model": model,
                "variant": str(candidate.get("variant", "")).strip(),
                "confidence": confidence,
                "evidence": candidate.get("evidence", []),
                "market_sample_count": 0,
                "reason": "Market validation search failed."
            }

        model_key = "".join(ch.lower() for ch in model if ch.isalnum())
        matched = []
        for item in results:
            title = str(item.get("title", ""))
            title_key = "".join(ch.lower() for ch in title if ch.isalnum())
            if model_key and model_key in title_key and item.get("price") is not None:
                matched.append(item)

        status = "VALIDATED" if len(matched) >= self.min_samples else "UNVERIFIED"

        return {
            "status": status,
            "brand": brand,
            "model": model,
            "variant": str(candidate.get("variant", "")).strip(),
            "confidence": confidence,
            "evidence": candidate.get("evidence", []),
            "market_sample_count": len(matched),
            "query": query,
            "reason": (
                "Candidate model was found in multiple marketplace listings."
                if status == "VALIDATED"
                else "Insufficient marketplace evidence to validate the candidate."
            )
        }
