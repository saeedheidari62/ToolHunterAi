from pathlib import Path
import json
import re


class ToolMatcher:

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

        self.tools = data["tools"]


    def normalize(self, text):

        text = text.lower()

        replacements = {
            "-": " ",
            "/": " ",
            "_": " "
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        text = re.sub(r"\s+", " ", text)

        return text.strip()


    def match(self, text):

        text = self.normalize(text)


        for tool in self.tools:

            candidates = []

            candidates.append(
                tool.get("name", "")
            )

            candidates.append(
                tool.get("brand", "")
            )

            candidates.extend(
                tool.get("aliases", [])
            )


            for candidate in candidates:

                candidate = self.normalize(candidate)

                if candidate and candidate in text:
                    return tool["id"]


        return None