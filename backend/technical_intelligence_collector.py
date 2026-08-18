from datetime import datetime, timezone


class TechnicalIntelligenceCollector:
    """Normalize technical facts without inventing unsupported specifications."""

    FIELD_ALIASES = {
        "voltage": ("voltage", "voltage_v", "v"),
        "power": ("power", "power_w", "wattage"),
        "battery": ("battery", "battery_type"),
        "rpm": ("rpm", "no_load_speed", "speed_rpm"),
        "torque": ("torque", "max_torque"),
        "chuck": ("chuck", "chuck_size"),
        "weight": ("weight", "weight_kg"),
        "dimensions": ("dimensions", "size"),
        "type": ("type", "tool_type", "category"),
    }

    def collect(self, candidate=None, description="", sources=None):
        candidate = candidate if isinstance(candidate, dict) else {}
        raw = candidate.get("technical_data")
        if not isinstance(raw, dict):
            raw = candidate.get("technical")
        if not isinstance(raw, dict):
            raw = {}

        technical = {}
        evidence = []
        provided_sources = list(sources or [])
        provided_sources.extend(candidate.get("technical_sources", []) or [])

        for field, aliases in self.FIELD_ALIASES.items():
            value = self._first_value(raw, aliases)
            if value is not None and value != "":
                technical[field] = value
                evidence.append({
                    "field": field,
                    "value": value,
                    "source": self._source_for(field, raw, provided_sources),
                    "confidence": "OBSERVED" if self._has_explicit_source(field, raw) else "PROVIDED",
                })

        # Preserve structured facts not covered by the standard fields.
        extra = raw.get("specifications")
        if isinstance(extra, dict):
            for key, value in extra.items():
                if value not in (None, "") and key not in technical:
                    technical[key] = value

        description = str(description or "").strip()
        if description and not technical:
            technical["description"] = description

        unique_sources = []
        for source in provided_sources:
            if source and source not in unique_sources:
                unique_sources.append(source)

        confidence = self._confidence(technical, evidence, unique_sources)
        return {
            "success": True,
            "technical": technical,
            "technical_evidence": evidence,
            "technical_sources": unique_sources,
            "technical_confidence": confidence,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def merge(self, existing, collected):
        existing = existing if isinstance(existing, dict) else {}
        collected = collected if isinstance(collected, dict) else {}
        technical = dict(existing.get("technical", {}))
        technical.update(collected.get("technical", {}))
        return {
            "technical": technical,
            "technical_evidence": list(existing.get("technical_evidence", [])) + list(collected.get("technical_evidence", [])),
            "technical_sources": self._unique(list(existing.get("technical_sources", [])) + list(collected.get("technical_sources", []))),
            "technical_confidence": collected.get("technical_confidence", existing.get("technical_confidence", "LOW")),
            "last_updated": collected.get("last_updated", existing.get("last_updated")),
        }

    def _first_value(self, data, aliases):
        for key in aliases:
            if key in data and data[key] not in (None, ""):
                return data[key]
        return None

    def _has_explicit_source(self, field, data):
        sources = data.get("sources")
        return isinstance(sources, dict) and bool(sources.get(field))

    def _source_for(self, field, data, fallback):
        sources = data.get("sources")
        if isinstance(sources, dict) and sources.get(field):
            return sources[field]
        return fallback[0] if fallback else "provided_data"

    def _confidence(self, technical, evidence, sources):
        if not technical:
            return "NONE"
        if evidence and sources:
            return "HIGH"
        if len(technical) >= 3:
            return "MEDIUM"
        return "LOW"

    def _unique(self, values):
        result = []
        for value in values:
            if value and value not in result:
                result.append(value)
        return result
