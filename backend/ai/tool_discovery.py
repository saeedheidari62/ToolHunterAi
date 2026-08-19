import json
import os
from urllib import request


class AIToolDiscovery:
    """Extract an unknown tool candidate without adding it to the KB."""

    def __init__(self, api_key=None, model=None, min_confidence=0.80):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("TOOLHUNTER_AI_MODEL", "gpt-5.6-luna")
        self.min_confidence = float(min_confidence)

    def enabled(self):
        return bool(self.api_key)

    def discover(self, text):
        if not self.enabled() or not str(text or "").strip():
            return None

        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": "Extract an industrial power tool candidate from marketplace text. Do not invent facts. Separate brand, model and variant when evidence supports them. If the model is unclear, return an empty model. This is discovery only: never claim that the candidate is already in the knowledge base."},
                {"role": "user", "content": str(text)},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "tool_discovery",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "brand": {"type": "string"},
                            "model": {"type": "string"},
                            "variant": {"type": "string"},
                            "candidate_tool_id": {"type": "string"},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "evidence": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["brand", "model", "variant", "candidate_tool_id", "confidence", "evidence"],
                        "additionalProperties": False,
                    },
                }
            },
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request("https://api.openai.com/v1/responses", data=data, headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, method="POST")
        try:
            with request.urlopen(req, timeout=30) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

        result = self._extract_result(raw)
        if not result:
            return None

        candidate_tool_id = str(result.get("candidate_tool_id", result.get("tool_id", ""))).strip()
        model = str(result.get("model", "")).strip()
        confidence = result.get("confidence", 0)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            return None
        if not candidate_tool_id and model:
            candidate_tool_id = model
        if not model and candidate_tool_id:
            model = candidate_tool_id
        if not model or confidence < self.min_confidence:
            return None

        return {
            "status": "CANDIDATE",
            "tool_id": candidate_tool_id,
            "candidate_tool_id": candidate_tool_id,
            "brand": str(result.get("brand", "")).strip(),
            "model": model,
            "variant": str(result.get("variant", "")).strip(),
            "confidence": confidence,
            "evidence": result.get("evidence", []),
        }

    def _extract_result(self, response):
        for item in response.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    try:
                        return json.loads(content.get("text", ""))
                    except (TypeError, ValueError):
                        return None
        return None
