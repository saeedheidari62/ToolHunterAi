from pathlib import Path
import json
import re
from datetime import datetime, timezone


class ToolKnowledgeBuilder:

    REQUIRED_FIELDS = [
        "tool_name", "category", "brand", "aliases", "technical",
        "common_failures", "inspection", "repair", "risk", "market",
        "confidence", "sources",
    ]

    def __init__(self):
        self.base_path = Path(__file__).resolve().parent.parent / "knowledge_base" / "tools"

    def validate(self, tool_data):
        if not isinstance(tool_data, dict):
            return {"valid": False, "errors": ["Tool data must be a dictionary."]}
        errors = []
        normalized = dict(tool_data)
        if "tool_name" not in normalized and "name" in normalized:
            normalized["tool_name"] = normalized["name"]
        for field in self.REQUIRED_FIELDS:
            if field not in normalized:
                errors.append(f"Missing required field: {field}")
        aliases = normalized.get("aliases")
        if aliases is not None and not isinstance(aliases, list):
            errors.append("Aliases must be a list.")
        sources = normalized.get("sources")
        if sources is not None and not isinstance(sources, list):
            errors.append("Sources must be a list.")
        market = normalized.get("market", {})
        if not isinstance(market, dict):
            errors.append("Market must be an object.")
        else:
            market_status = str(market.get("status", "available")).strip().lower()
            for field in ("used_price_min", "used_price_max"):
                if field not in market:
                    errors.append(f"Missing market field: {field}")
            if market_status != "unavailable":
                if "used_price_min" in market and "used_price_max" in market:
                    try:
                        low, high = float(market["used_price_min"]), float(market["used_price_max"])
                        if low <= 0 or high <= 0:
                            errors.append("Market prices must be greater than zero.")
                        elif low > high:
                            errors.append("used_price_min cannot be greater than used_price_max.")
                    except (TypeError, ValueError):
                        errors.append("Market prices must be numeric.")
            sample_count = market.get("sample_count")
            if sample_count is not None:
                try:
                    if int(sample_count) < 0:
                        errors.append("Market sample_count cannot be negative.")
                except (TypeError, ValueError):
                    errors.append("Market sample_count must be numeric.")
            median = market.get("median_price")
            if median is not None:
                try:
                    if float(median) <= 0 and market_status != "unavailable":
                        errors.append("Market median_price must be greater than zero.")
                except (TypeError, ValueError):
                    errors.append("Market median_price must be numeric.")
            confidence = market.get("price_confidence")
            if isinstance(confidence, str):
                confidence = {"HIGH": 0.9, "MEDIUM": 0.7, "LOW": 0.4, "NONE": 0.0}.get(confidence.strip().upper())
            if confidence is not None:
                try:
                    confidence = float(confidence)
                    if not 0 <= confidence <= 1:
                        errors.append("Market price_confidence must be between 0 and 1.")
                except (TypeError, ValueError):
                    errors.append("Market price_confidence must be numeric.")
            market_sources = market.get("sources")
            if market_sources is not None and not isinstance(market_sources, list):
                errors.append("Market sources must be a list.")
        return {"valid": len(errors) == 0, "errors": errors}

    def make_tool_id(self, brand, tool_name):
        value = f"{str(brand or '').strip().lower()} {str(tool_name or '').strip().lower()}"
        value = re.sub(r"\s+", " ", value.replace("-", " ").replace("/", " ").replace(".", " ")).strip()
        parts = value.split()
        return f"{parts[0]}_{''.join(parts[1:])}" if parts else ""

    def normalize_technical(self, technical, sources=None):
        if not isinstance(technical, dict):
            return {"success": False, "errors": ["Technical data must be an object."]}
        normalized = dict(technical)
        aliases = {"voltage_v": "voltage", "power_w": "power", "wattage": "power", "battery_type": "battery", "no_load_speed": "rpm", "speed_rpm": "rpm", "max_torque": "torque", "chuck_size": "chuck", "weight_kg": "weight", "size": "dimensions", "tool_type": "type"}
        for source_key, target_key in aliases.items():
            if target_key not in normalized and source_key in normalized:
                normalized[target_key] = normalized[source_key]
        merged_sources = list(sources or [])
        if isinstance(normalized.get("sources"), list): merged_sources.extend(normalized["sources"])
        normalized["sources"] = list(dict.fromkeys(x for x in merged_sources if x))
        normalized["last_updated"] = normalized.get("last_updated", datetime.now(timezone.utc).isoformat())
        return {"success": True, "technical": normalized}

    def normalize_market(self, market, sources=None):
        if not isinstance(market, dict): return {"success": False, "errors": ["Market must be an object."]}
        normalized = dict(market)
        aliases = {"min_price": "used_price_min", "max_price": "used_price_max", "median": "median_price", "count": "sample_count", "confidence": "price_confidence"}
        for source_key, target_key in aliases.items():
            if target_key not in normalized and source_key in normalized: normalized[target_key] = normalized[source_key]
        normalized.setdefault("sample_count", 0)
        if "median_price" not in normalized:
            low, high = normalized.get("used_price_min"), normalized.get("used_price_max")
            if low is not None and high is not None:
                try: normalized["median_price"] = (float(low) + float(high)) / 2
                except (TypeError, ValueError): pass
        confidence = normalized.get("price_confidence")
        if isinstance(confidence, str): normalized["price_confidence"] = {"HIGH": 0.9, "MEDIUM": 0.7, "LOW": 0.4, "NONE": 0.0}.get(confidence.strip().upper(), 0.0)
        elif confidence is None:
            try: normalized["price_confidence"] = min(1.0, int(normalized.get("sample_count", 0)) / 10.0)
            except (TypeError, ValueError): normalized["price_confidence"] = 0.0
        else:
            try: normalized["price_confidence"] = float(confidence)
            except (TypeError, ValueError): normalized["price_confidence"] = 0.0
        normalized["sources"] = list(sources) if sources is not None else (normalized.get("sources") if isinstance(normalized.get("sources"), list) else [])
        normalized["last_updated"] = normalized.get("last_updated", datetime.now(timezone.utc).isoformat())
        return {"success": True, "market": normalized}

    def create_draft(self, tool_name, brand="", category=""):
        tool_name, brand, category = str(tool_name or "").strip(), str(brand or "").strip(), str(category or "").strip()
        if not tool_name: return {"success": False, "errors": ["Tool name is required."]}
        return {"success": True, "tool": {"tool_name": tool_name, "category": category, "brand": brand, "aliases": [tool_name], "technical": {}, "common_failures": [], "inspection": [], "repair": {}, "risk": {}, "market": {"used_price_min": None, "used_price_max": None, "median_price": None, "sample_count": 0, "price_confidence": 0.0, "sources": [], "status": "unavailable", "last_updated": None}, "confidence": "draft", "sources": []}}

    def enrich(self, draft, enrichment):
        if not isinstance(draft, dict): return {"success": False, "errors": ["Draft must be a dictionary."]}
        if not isinstance(enrichment, dict): return {"success": False, "errors": ["Enrichment must be a dictionary."]}
        enriched = dict(draft)
        for field in ("category", "brand", "aliases", "technical", "common_failures", "inspection", "repair", "risk", "confidence", "sources"):
            if field in enrichment: enriched[field] = enrichment[field]
        if "technical" in enrichment:
            result = self.normalize_technical(enrichment["technical"], enrichment.get("technical_sources"))
            if not result["success"]: return result
            enriched["technical"] = result["technical"]
        if "market" in enrichment:
            result = self.normalize_market(enrichment["market"], enrichment.get("sources"))
            if not result["success"]: return result
            enriched["market"] = result["market"]
        validation = self.validate(enriched)
        return {"success": True, "tool": enriched} if validation["valid"] else {"success": False, "errors": validation["errors"], "tool": enriched}

    def build(self, tool_data):
        if not isinstance(tool_data, dict): return {"success": False, "errors": ["Tool data must be a dictionary."]}
        normalized = dict(tool_data)
        if "tool_name" not in normalized and "name" in normalized: normalized["tool_name"] = normalized["name"]
        market_result = self.normalize_market(normalized.get("market", {}))
        if market_result["success"]:
            normalized["market"] = market_result["market"]
        technical_result = self.normalize_technical(normalized.get("technical", {}))
        if technical_result["success"]:
            normalized["technical"] = technical_result["technical"]
        validation = self.validate(normalized)
        return {"success": True, "tool": normalized} if validation["valid"] else {"success": False, "errors": validation["errors"]}

    def save(self, tool_id, tool_data):
        result = self.build(tool_data)
        if not result["success"]: return result
        file_path = self.base_path / f"{tool_id}.json"
        with open(file_path, "w", encoding="utf-8") as file: json.dump(result["tool"], file, ensure_ascii=False, indent=2)
        return {"success": True, "tool_id": tool_id, "file": str(file_path)}
