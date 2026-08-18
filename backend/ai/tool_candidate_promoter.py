import json
import re
from pathlib import Path


class ToolCandidatePromoter:
    """Promote only validated, evidence-backed candidates into the Knowledge Base."""

    def __init__(self, knowledge_dir="knowledge_base/tools", min_samples=2, min_confidence=0.80):
        self.knowledge_dir = Path(knowledge_dir)
        self.index_path = self.knowledge_dir / "tools_index.json"
        self.min_samples = int(min_samples)
        self.min_confidence = float(min_confidence)

    def _slug(self, brand, model, variant=""):
        value = "_".join(part for part in [brand, model, variant] if str(part).strip())
        value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
        return value.lower()

    def _build_default_knowledge(self, candidate):
        brand = str(candidate.get("brand", "")).strip()
        model = str(candidate.get("model", "")).strip()
        variant = str(candidate.get("variant", "")).strip()
        confidence = float(candidate.get("confidence", 0))
        evidence = candidate.get("evidence", [])
        market_sample_count = int(candidate.get("market_sample_count", 0))
        market_data = candidate.get("market_data")
        if not isinstance(market_data, dict):
            market_data = {}

        technical_data = candidate.get("technical_data")
        if not isinstance(technical_data, dict):
            technical_data = candidate.get("technical")
        if not isinstance(technical_data, dict):
            technical_data = {}

        return {
            "tool_name": f"{brand} {model}".strip(),
            "brand": brand,
            "technical": technical_data,
            "brand_info": {"score": 0},
            "market": {
                "new_price": market_data.get("new_price"),
                "used_price_min": market_data.get("used_price_min"),
                "used_price_max": market_data.get("used_price_max"),
                "median_price": market_data.get("median_price"),
                "sample_count": market_data.get("sample_count", market_sample_count),
                "price_confidence": market_data.get("price_confidence", "MEDIUM"),
                "sources": market_data.get("sources", ["divar"]),
                "last_updated": market_data.get("last_updated"),
            },
            "common_failures": candidate.get("common_failures", []),
            "inspection": candidate.get("inspection", []),
            "risk": candidate.get("risk", {"score": 50, "level": "Medium"}),
            "buy_score": candidate.get("buy_score", 50),
            "recommendation": candidate.get("recommendation", "REVIEW"),
            "discovery": {
                "variant": variant,
                "confidence": confidence,
                "evidence": evidence,
                "market_sample_count": market_sample_count,
                "technical_sources": candidate.get("technical_sources", []),
            },
        }

    def promote(self, candidate, knowledge=None):
        if not isinstance(candidate, dict) or candidate.get("status") != "VALIDATED":
            return {"status": "REJECTED", "reason": "Candidate is not validated."}

        brand = str(candidate.get("brand", "")).strip()
        model = str(candidate.get("model", "")).strip()
        variant = str(candidate.get("variant", "")).strip()
        evidence = candidate.get("evidence", [])
        try:
            confidence = float(candidate.get("confidence", 0))
        except (TypeError, ValueError):
            confidence = 0
        try:
            market_sample_count = int(candidate.get("market_sample_count", 0))
        except (TypeError, ValueError):
            market_sample_count = 0

        if not brand or not model:
            return {"status": "REJECTED", "reason": "Brand and model are required."}
        if confidence < self.min_confidence:
            return {"status": "REJECTED", "reason": "Discovery confidence is below promotion threshold."}
        if market_sample_count < self.min_samples:
            return {"status": "REJECTED", "reason": "Insufficient marketplace evidence for promotion."}
        if not isinstance(evidence, list) or not evidence:
            return {"status": "REJECTED", "reason": "Evidence is required for promotion."}

        tool_id = self._slug(brand, model, variant)
        filename = f"{tool_id}.json"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        tool_path = self.knowledge_dir / filename

        if tool_path.exists():
            return {"status": "EXISTS", "tool_id": tool_id, "file": filename}

        data = knowledge if isinstance(knowledge, dict) else self._build_default_knowledge(candidate)

        with tool_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)

        if self.index_path.exists():
            with self.index_path.open("r", encoding="utf-8") as handle:
                index = json.load(handle)
        else:
            index = {"tools": []}

        index.setdefault("tools", []).append({
            "id": tool_id,
            "name": f"{brand} {model}".strip(),
            "brand": brand,
            "category": data.get("category", "toolbox"),
            "file": filename,
            "aliases": [model, f"{brand} {model}".strip()],
        })

        with self.index_path.open("w", encoding="utf-8") as handle:
            json.dump(index, handle, ensure_ascii=False, indent=2)

        return {
            "status": "PROMOTED",
            "tool_id": tool_id,
            "file": filename,
            "market_sample_count": market_sample_count,
        }
