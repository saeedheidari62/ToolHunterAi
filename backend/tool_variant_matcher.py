import re


class ToolVariantMatcher:

    def detect_bosch_gbh_2_26_variant(self, text):
        text = str(text or "").lower()

        if re.search(
            r"\bgbh[\s-]*2[\s-]*26[\s-]*dfr\b",
            text
        ):
            return "DFR"

        if re.search(
            r"\bgbh[\s-]*2[\s-]*26[\s-]*dre\b",
            text
        ):
            return "DRE"

        if re.search(
            r"\bgbh[\s-]*2[\s-]*26\b",
            text
        ):
            return "BASE"

        return None

    def detect(self, text, tool_id=None):
        if tool_id == "bosch_gbh_2_26":
            return self.detect_bosch_gbh_2_26_variant(text)

        return None
