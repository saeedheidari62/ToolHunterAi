from pathlib import Path
import json
import re


class MultiToolAnalyzer:

    DIGIT_MAP = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹",
        "0123456789"
    )

    def __init__(self):
        base_path = Path(__file__).resolve().parent.parent
        index_path = (
            base_path
            / "knowledge_base"
            / "tools"
            / "tools_index.json"
        )

        with open(index_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.tools = data.get("tools", [])

    def normalize(self, text):
        text = str(text or "").lower()
        text = text.translate(self.DIGIT_MAP)

        replacements = {
            "ي": "ی",
            "ى": "ی",
            "ك": "ک",
            "‌": " ",
            "-": " ",
            "_": " ",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return re.sub(r"\s+", " ", text).strip()

    def _get_candidates(self, tool):
        candidates = []

        if tool.get("name"):
            candidates.append(tool["name"])

        candidates.extend(tool.get("aliases", []))

        return [
            self.normalize(x)
            for x in candidates
            if self.normalize(x)
        ]

    def _find_mentions(self, text, tool_ids):
        normalized = self.normalize(text)
        mentions = []

        for tool in self.tools:
            tool_id = tool.get("id")

            if tool_id not in tool_ids:
                continue

            for candidate in self._get_candidates(tool):
                position = normalized.find(candidate)

                if position >= 0:
                    mentions.append({
                        "tool_id": tool_id,
                        "position": position,
                        "candidate": candidate
                    })
                    break

        return sorted(
            mentions,
            key=lambda item: item["position"]
        )

    def _extract_price(self, text):
        normalized = self.normalize(text)

        pattern = re.compile(
            r'(?:قیمت|مبلغ)\s*'
            r'(?P<price>\d[\d\s,\\.]{3,})'
        )

        match = pattern.search(normalized)

        if not match:
            return None

        raw = match.group("price")

        digits = re.sub(
            r"[^\d]",
            "",
            raw
        )

        if not digits:
            return None

        try:
            return int(digits)
        except ValueError:
            return None

    def analyze(self, description, tool_ids):
        text = self.normalize(description)

        if not text or not tool_ids:
            return {
                "tools": [],
                "confidence": "low"
            }

        mentions = self._find_mentions(
            text,
            tool_ids
        )

        results = []

        for index, mention in enumerate(mentions):
            start = mention["position"]

            if index + 1 < len(mentions):
                end = mentions[index + 1]["position"]
            else:
                end = len(text)

            segment = text[start:end]

            results.append({
                "tool_id": mention["tool_id"],
                "asking_price": self._extract_price(segment),
                "text": segment
            })

        if not results:
            confidence = "low"
        elif all(
            item["asking_price"] is not None
            for item in results
        ):
            confidence = "high"
        else:
            confidence = "medium"

        return {
            "tools": results,
            "confidence": confidence
        }
