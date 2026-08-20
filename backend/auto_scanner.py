import json
from pathlib import Path


class AutoScanner:
    """Run bounded discovery across the configured tool catalog."""

    MAX_TOOLS = 8
    DEFAULT_LIMIT_PER_TOOL = 5

    def __init__(self, catalog_path=None, discovery_service=None):
        self.catalog_path = Path(catalog_path or Path(__file__).resolve().parent.parent / "knowledge_base" / "tools" / "tools_index.json")
        self.discovery_service = discovery_service

    def load_catalog(self):
        with self.catalog_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        tools = data.get("tools", []) if isinstance(data, dict) else []
        return [tool for tool in tools if isinstance(tool, dict) and tool.get("id")][: self.MAX_TOOLS]

    @staticmethod
    def _global_rank(results):
        return sorted(
            results,
            key=lambda item: (
                {"BUY": 3, "REVIEW": 2, "DON'T BUY": 1}.get(item.get("decision", "REVIEW"), 1),
                item.get("final_score", 0),
                item.get("buy_score", 0),
                -item.get("risk_score", 100),
            ),
            reverse=True,
        )

    def scan(self, city, limit_per_tool=DEFAULT_LIMIT_PER_TOOL):
        if not str(city or "").strip():
            return {"error": "INVALID_SCAN_INPUT", "message": "city is required."}
        try:
            limit_per_tool = int(limit_per_tool)
        except (TypeError, ValueError):
            limit_per_tool = self.DEFAULT_LIMIT_PER_TOOL
        limit_per_tool = max(1, min(limit_per_tool, self.DEFAULT_LIMIT_PER_TOOL))

        if self.discovery_service is None:
            from .discovery_service import DiscoveryService
            self.discovery_service = DiscoveryService()

        tools = self.load_catalog()
        tool_runs = []
        opportunities = []
        errors = []

        for tool in tools:
            try:
                result = self.discovery_service.discover(
                    city=str(city).strip(),
                    query=tool.get("name", ""),
                    limit=limit_per_tool,
                )
                if not isinstance(result, dict):
                    errors.append({"tool_id": tool["id"], "error": "INVALID_DISCOVERY_RESULT"})
                    continue
                tool_runs.append({
                    "tool_id": tool["id"],
                    "tool_name": tool.get("name", ""),
                    "searched": result.get("searched", 0),
                    "filtered": result.get("filtered", 0),
                    "selected": result.get("selected", 0),
                    "analyzed": result.get("analyzed", 0),
                    "best_choice": result.get("best_choice"),
                    "search_batches": result.get("search_batches", 0),
                })
                for item in result.get("ranking", []):
                    if isinstance(item, dict):
                        enriched = dict(item)
                        enriched["tool_id"] = tool["id"]
                        enriched["tool_name"] = tool.get("name", "")
                        opportunities.append(enriched)
            except Exception as exc:
                errors.append({"tool_id": tool["id"], "error": type(exc).__name__})

        ranking = self._global_rank(opportunities)
        return {
            "city": str(city).strip(),
            "tools_scanned": len(tools),
            "tools_completed": len(tool_runs),
            "opportunities": len(ranking),
            "tool_runs": tool_runs,
            "ranking": ranking,
            "best_choice": ranking[0] if ranking else None,
            "errors": errors,
        }
