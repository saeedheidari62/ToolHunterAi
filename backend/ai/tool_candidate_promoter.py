import json
import os
import re
from pathlib import Path


class ToolCandidatePromoter:
    """Promote only validated candidates into the Knowledge Base."""

    def __init__(self, knowledge_dir="knowledge_base/tools"):
        self.knowledge_dir = Path(knowledge_dir)
        self.index_path = self.knowledge_dir / "tools_index.json"

    def _slug(self, brand, model, variant=""):
        value = "_".join(
            part for part in [brand, model, variant] if str(part).strip()
        )
        value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
        return value.lower()

    def promote(self, candidate, knowledge=None):
        if not isinstance(candidate, dict) or candidate.get("status") != "VALIDATED":
            return {"status": "REJECTED", "reason": "Candidate is not validated."}

        brand = str(candidate.get("brand", "")).strip()
        model = str(candidate.get("model", "")).strip()
        variant = str(candidate.get("variant", "")).strip()
        if not brand or not model:
            return {"status": "REJECTED", "reason": "Brand and model are required."}

        tool_id = self._slug(brand, model, variant)
        filename = f"{tool_id}.json"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        tool_path = self.knowledge_dir / filename

        if tool_path.exists():
            return {"status": "EXISTS", "tool_id": tool_id, "file": filename}

        data = knowledge if isinstance(knowledge, dict) else {
            "tool_name": f"{brand} {model}".strip(),
            "brand": brand,
            "technical": {"score": 0},
            "brand_info": {"score": 0},
            "market": {
                "new_price": None,
                "used_price_min": None,
                "used_price_max": None,
            },
            "common_failures": [],
            "inspection": [],
            "risk": {"score": 50, "level": "Medium"},
            "buy_score": 50,
            "recommendation": "REVIEW",
            "discovery": {
                "variant": variant,
                "confidence": candidate.get("confidence", 0),
                "evidence": candidate.get("evidence", []),
            },
        }

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
        }
