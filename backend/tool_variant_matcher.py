import re


class ToolVariantMatcher:

    def _normalize(self, text):
        text = str(text or "").lower()
        text = text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
        text = text.replace("–", "-").replace("—", "-")
        return re.sub(r"\s+", " ", text).strip()

    def detect_bosch_gbh_2_26_variant(self, text):
        text = self._normalize(text)

        if re.search(r"\bgbh[\s-]*2[\s-]*26[\s-]*dfr\b", text):
            return "DFR"
        if re.search(r"\bgbh[\s-]*2[\s-]*26[\s-]*dre\b", text):
            return "DRE"
        if re.search(r"\bgbh[\s-]*2[\s-]*26\b", text):
            return "BASE"
        return None

    def detect(self, text, tool_id=None):
        if tool_id == "bosch_gbh_2_26":
            return self.detect_bosch_gbh_2_26_variant(text)
        return None
