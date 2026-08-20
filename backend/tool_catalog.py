import json
from pathlib import Path


class ToolCatalog:
    """Read the canonical tool catalog from the knowledge base."""

    INDEX_PATH = Path(__file__).resolve().parent.parent / "knowledge_base" / "tools" / "tools_index.json"

    def __init__(self, index_path=None):
        self.index_path = Path(index_path) if index_path else self.INDEX_PATH

    def all(self):
        with self.index_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        tools = data.get("tools", [])
        return [tool for tool in tools if isinstance(tool, dict) and tool.get("id")]

    def ids(self):
        return [tool["id"] for tool in self.all()]

    def get(self, tool_id):
        for tool in self.all():
            if tool.get("id") == tool_id:
                return tool
        return None

    def select(self, tool_ids=None):
        tools = self.all()
        if not tool_ids:
            return tools
        requested = set(tool_ids)
        return [tool for tool in tools if tool.get("id") in requested]
