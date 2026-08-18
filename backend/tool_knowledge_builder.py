from pathlib import Path
import json
import re
from datetime import datetime, timezone


class ToolKnowledgeBuilder:

    REQUIRED_FIELDS = [
        "tool_name",
        "category",
        "brand",
        "aliases",
        "technical",
        "common_failures",
        "inspection",
        "repair",
        "risk",
        "market",
        "confidence",
        "sources",
    ]

    def __init__(self):
        self.base_path = (
            Path(__file__).resolve().parent.parent
            / "knowledge_base"
            / "tools"
        )

    def validate(self, tool_data):
        if not isinstance(tool_data, dict):
            return {
                "valid": False,
                "errors": ["Tool data must be a dictionary."]
            }

        errors = []

        for field in self.REQUIRED_FIELDS:
            if field not in tool_data:
                errors.append(
                    f"Missing required field: {field}"
                )

        market = tool_data.get("market", {})

        if not isinstance(market, dict):
            errors.append("Market must be an object.")
        else:
            for field in (
                "used_price_min",
                "used_price_max",
            ):
                if field not in market:
                    errors.append(
                        f"Missing market field: {field}"
                    )

            if (
                "used_price_min" in market
                and "used_price_max" in market
            ):
                try:
                    low = float(market["used_price_min"])
                    high = float(market["used_price_max"])

                    if low <= 0 or high <= 0:
                        errors.append(
                            "Market prices must be greater than zero."
                        )

                    elif low > high:
                        errors.append(
                            "used_price_min cannot be greater than used_price_max."
                        )

                except (TypeError, ValueError):
                    errors.append(
                        "Market prices must be numeric."
                    )

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
                    if float(median) <= 0:
                        errors.append("Market median_price must be greater than zero.")
                except (TypeError, ValueError):
                    errors.append("Market median_price must be numeric.")

            confidence = market.get("price_confidence")
            if confidence is not None:
                try:
                    confidence = float(confidence)
                    if not 0 <= confidence <= 1:
                        errors.append("Market price_confidence must be between 0 and 1.")
                except (TypeError, ValueError):
                    errors.append("Market price_confidence must be numeric.")

            sources = market.get("sources")
            if sources is not None and not isinstance(sources, list):
                errors.append("Market sources must be a list.")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def make_tool_id(self, brand, tool_name):
        brand = str(brand or "").strip().lower()
        tool_name = str(tool_name or "").strip().lower()

        value = f"{brand} {tool_name}"

        value = value.replace("-", " ")
        value = value.replace("/", " ")
        value = value.replace(".", " ")

        value = re.sub(r"\s+", " ", value).strip()

        parts = value.split()

        if not parts:
            return ""

        brand_part = parts[0]
        model_part = "".join(parts[1:])

        return f"{brand_part}_{model_part}"

    def normalize_market(self, market, sources=None):
        if not isinstance(market, dict):
            return {
                "success": False,
                "errors": ["Market must be an object."]
            }

        normalized = dict(market)

        aliases = {
            "min_price": "used_price_min",
            "max_price": "used_price_max",
            "median": "median_price",
            "count": "sample_count",
            "confidence": "price_confidence",
        }

        for source_key, target_key in aliases.items():
            if target_key not in normalized and source_key in normalized:
                normalized[target_key] = normalized[source_key]

        if "sample_count" not in normalized:
            normalized["sample_count"] = 0

        if "median_price" not in normalized:
            low = normalized.get("used_price_min")
            high = normalized.get("used_price_max")
            if low is not None and high is not None:
                try:
                    normalized["median_price"] = (
                        float(low) + float(high)
                    ) / 2
                except (TypeError, ValueError):
                    pass

        if "price_confidence" not in normalized:
            try:
                count = int(normalized.get("sample_count", 0))
            except (TypeError, ValueError):
                count = 0
            normalized["price_confidence"] = min(1.0, count / 10.0)

        if sources is not None:
            normalized["sources"] = list(sources)
        elif not isinstance(normalized.get("sources"), list):
            normalized["sources"] = []

        normalized["last_updated"] = normalized.get(
            "last_updated",
            datetime.now(timezone.utc).isoformat()
        )

        return {
            "success": True,
            "market": normalized
        }

    def create_draft(self, tool_name, brand="", category=""):
        tool_name = str(tool_name or "").strip()
        brand = str(brand or "").strip()
        category = str(category or "").strip()

        if not tool_name:
            return {
                "success": False,
                "errors": ["Tool name is required."]
            }

        draft = {
            "tool_name": tool_name,
            "category": category,
            "brand": brand,
            "aliases": [tool_name],
            "technical": {},
            "common_failures": [],
            "inspection": [],
            "repair": {},
            "risk": {},
            "market": {
                "used_price_min": None,
                "used_price_max": None,
                "median_price": None,
                "sample_count": 0,
                "price_confidence": 0.0,
                "sources": [],
                "last_updated": None
            },
            "confidence": "draft",
            "sources": []
        }

        return {
            "success": True,
            "tool": draft
        }

    def enrich(self, draft, enrichment):
        if not isinstance(draft, dict):
            return {
                "success": False,
                "errors": ["Draft must be a dictionary."]
            }

        if not isinstance(enrichment, dict):
            return {
                "success": False,
                "errors": ["Enrichment must be a dictionary."]
            }

        enriched = dict(draft)

        for field in (
            "category",
            "brand",
            "aliases",
            "technical",
            "common_failures",
            "inspection",
            "repair",
            "risk",
            "confidence",
            "sources",
        ):
            if field in enrichment:
                enriched[field] = enrichment[field]

        if "market" in enrichment:
            market_result = self.normalize_market(
                enrichment["market"],
                enrichment.get("sources")
            )
            if not market_result["success"]:
                return market_result
            enriched["market"] = market_result["market"]

        validation = self.validate(enriched)

        if not validation["valid"]:
            return {
                "success": False,
                "errors": validation["errors"],
                "tool": enriched
            }

        return {
            "success": True,
            "tool": enriched
        }

    def build(self, tool_data):
        validation = self.validate(tool_data)

        if not validation["valid"]:
            return {
                "success": False,
                "errors": validation["errors"]
            }

        return {
            "success": True,
            "tool": tool_data
        }

    def save(self, tool_id, tool_data):
        result = self.build(tool_data)

        if not result["success"]:
            return result

        file_path = self.base_path / f"{tool_id}.json"

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                tool_data,
                file,
                ensure_ascii=False,
                indent=2
            )

        return {
            "success": True,
            "tool_id": tool_id,
            "file": str(file_path)
        }
