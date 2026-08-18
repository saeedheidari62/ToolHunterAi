import json
import os
from pathlib import Path
from urllib import request


class AIToolResolver:
    """Optional AI fallback for ambiguous or unrecognized tool text."""

    def __init__(self, api_key=None, model=None, min_confidence=0.85):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("TOOLHUNTER_AI_MODEL", "gpt-5.6-luna")
        self.min_confidence = float(min_confidence)
        self.tools = self._load_tools()

    def _load_tools(self):
        index_path = (
            Path(__file__).resolve().parent.parent.parent
            / "knowledge_base"
            / "tools"
            / "tools_index.json"
        )

        with open(index_path, "r", encoding="utf-8") as file:
            return json.load(file).get("tools", [])

    def enabled(self):
        return bool(self.api_key and self.tools)

    def _tool_catalog(self):
        return [
            {
                "id": tool.get("id"),
                "name": tool.get("name", ""),
                "aliases": tool.get("aliases", []),
            }
            for tool in self.tools
        ]

    def resolve(self, text):
        if not self.enabled():
            return None

        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "You identify industrial power tools from marketplace text. "
                        "Only choose a tool from the supplied catalog. Never invent a tool ID. "
                        "If evidence is insufficient, return an empty candidate_tool_id. "
                        "Confidence must represent evidence strength, not certainty from guessing."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "ad_text": str(text or ""),
                            "tool_catalog": self._tool_catalog(),
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "tool_resolution",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "candidate_tool_id": {"type": "string"},
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "evidence": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": [
                            "candidate_tool_id",
                            "confidence",
                            "evidence",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
        }

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            "https://api.openai.com/v1/responses",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=30) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

        result = self._extract_result(raw)
        if not result:
            return None

        candidate = result.get("candidate_tool_id", "")
        confidence = result.get("confidence", 0)

        known_ids = {tool.get("id") for tool in self.tools}
        if not candidate or candidate not in known_ids or confidence < self.min_confidence:
            return None

        return {
            "tool_id": candidate,
            "confidence": confidence,
            "evidence": result.get("evidence", []),
        }

    def _extract_result(self, response):
        output = response.get("output", [])

        for item in output:
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    text = content.get("text", "")
                    try:
                        return json.loads(text)
                    except (TypeError, ValueError):
                        return None

        return None
