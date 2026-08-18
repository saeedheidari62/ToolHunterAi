from datetime import datetime, timezone


class EvidenceLayer:
    """Normalize and score technical, market, and discovery evidence."""

    CONFIDENCE_MAP = {
        "HIGH": 0.90,
        "MEDIUM": 0.70,
        "LOW": 0.40,
        "NONE": 0.0,
        "OBSERVED": 0.90,
        "PROVIDED": 0.70,
    }

    def __init__(self, minimum_sources=1):
        self.minimum_sources = int(minimum_sources)

    def _source_list(self, value):
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            return []
        return list(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))

    def _confidence_value(self, value):
        if isinstance(value, str):
            normalized = value.strip().upper()
            if normalized in self.CONFIDENCE_MAP:
                return self.CONFIDENCE_MAP[normalized]
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return None

    def build(self, discovery=None, technical=None, market=None):
        discovery = discovery if isinstance(discovery, dict) else {}
        technical = technical if isinstance(technical, dict) else {}
        market = market if isinstance(market, dict) else {}

        sources = []
        sources.extend(self._source_list(discovery.get("sources") or discovery.get("evidence")))
        sources.extend(self._source_list(technical.get("sources") or technical.get("technical_sources")))
        sources.extend(self._source_list(market.get("sources")))
        sources = list(dict.fromkeys(sources))

        components = {
            "discovery": bool(discovery),
            "technical": bool(technical),
            "market": bool(market),
        }
        component_count = sum(components.values())
        source_score = min(1.0, len(sources) / 3.0)
        coverage_score = component_count / 3.0

        confidence_values = []
        for value in (
            discovery.get("confidence"),
            technical.get("confidence", technical.get("technical_confidence")),
            market.get("price_confidence", market.get("confidence")),
        ):
            normalized = self._confidence_value(value)
            if normalized is not None:
                confidence_values.append(normalized)
        confidence_score = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
        overall = round((coverage_score * 0.4) + (source_score * 0.3) + (confidence_score * 0.3), 3)

        return {
            "components": components,
            "sources": sources,
            "source_count": len(sources),
            "coverage_score": round(coverage_score, 3),
            "confidence_score": round(confidence_score, 3),
            "overall_confidence": overall,
            "sufficient": bool(sources) and len(sources) >= self.minimum_sources and component_count > 0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
