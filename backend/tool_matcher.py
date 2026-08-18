from pathlib import Path
import json
import re


class ToolMatcher:

    def __init__(self):
        self._index_path = (
            Path(__file__).resolve().parent.parent
            / "knowledge_base"
            / "tools"
            / "tools_index.json"
        )
        self._index_mtime = None
        self.reload()

    def reload(self):
        with open(self._index_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.tools = data.get("tools", [])
        try:
            self._index_mtime = self._index_path.stat().st_mtime_ns
        except OSError:
            self._index_mtime = None
        return len(self.tools)

    def reload_if_changed(self):
        try:
            current_mtime = self._index_path.stat().st_mtime_ns
        except OSError:
            return False
        if self._index_mtime != current_mtime:
            self.reload()
            return True
        return False

    def normalize(self, text):
        text = str(text or "").lower()
        replacements = {"-": " ", "/": " ", "_": " "}
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def match_all(self, text):
        self.reload_if_changed()
        text = self.normalize(text)
        matches = []
        for tool in self.tools:
            candidates = [tool.get("name", "")]
            candidates.extend(tool.get("aliases", []))
            found = False
            for candidate in candidates:
                candidate = self.normalize(candidate)
                if not candidate:
                    continue
                if not re.search(r"\d", candidate):
                    continue
                if candidate in text:
                    found = True
                    break
            if found:
                matches.append(tool["id"])
        return matches

    def match(self, text):
        matches = self.match_all(text)
        if not matches:
            return None
        return matches[0]
