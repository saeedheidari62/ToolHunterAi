import json
from pathlib import Path

from .opportunity_engine import OpportunityEngine


class AutoScanner:
    """Run bounded discovery across the configured tool catalog and cities."""

    MAX_TOOLS = 8
    MAX_CITIES = 6
    DEFAULT_LIMIT_PER_TOOL = 5

    def __init__(self, catalog_path=None, discovery_service=None, opportunity_engine=None):
        self.catalog_path = Path(catalog_path or Path(__file__).resolve().parent.parent / "knowledge_base" / "tools" / "tools_index.json")
        self.discovery_service = discovery_service
        self.opportunity_engine = opportunity_engine or OpportunityEngine()

    def load_catalog(self):
        with self.catalog_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        tools = data.get("tools", []) if isinstance(data, dict) else []
        return [tool for tool in tools if isinstance(tool, dict) and tool.get("id")][: self.MAX_TOOLS]

    def _select_tools(self, tool_ids=None):
        tools = self.load_catalog()
        if not tool_ids:
            return tools
        requested = {str(tool_id).strip() for tool_id in tool_ids if str(tool_id).strip()}
        return [tool for tool in tools if tool.get("id") in requested]

    @staticmethod
    def _candidate_key(item):
        return item.get("token") or item.get("url") or item.get("id")

    def _deduplicate(self, results):
        seen = set()
        unique = []
        for item in results:
            if not isinstance(item, dict):
                continue
            key = self._candidate_key(item)
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            unique.append(item)
        return unique

    def _global_rank(self, results, limit=None):
        return self.opportunity_engine.rank(self._deduplicate(results), limit=limit)

    def scan(self, city, limit_per_tool=DEFAULT_LIMIT_PER_TOOL, tool_ids=None, top_n=None):
        return self.scan_cities([city], limit_per_tool=limit_per_tool, tool_ids=tool_ids, top_n=top_n)

    def scan_cities(self, cities, limit_per_tool=DEFAULT_LIMIT_PER_TOOL, top_n=None, tool_ids=None):
        if isinstance(cities, str):
            cities = [cities]
        cities = [str(city).strip() for city in (cities or []) if str(city).strip()]
        if not cities:
            return {"error": "INVALID_SCAN_INPUT", "message": "at least one city is required."}
        cities = cities[: self.MAX_CITIES]
        try:
            limit_per_tool = int(limit_per_tool)
        except (TypeError, ValueError):
            limit_per_tool = self.DEFAULT_LIMIT_PER_TOOL
        limit_per_tool = max(1, min(limit_per_tool, self.DEFAULT_LIMIT_PER_TOOL))
        try:
            top_n = None if top_n is None else max(1, min(int(top_n), 50))
        except (TypeError, ValueError):
            return {"error": "INVALID_SCAN_INPUT", "message": "top_n must be an integer."}

        if self.discovery_service is None:
            from .discovery_service import DiscoveryService
            self.discovery_service = DiscoveryService()

        tools = self._select_tools(tool_ids)
        if tool_ids and not tools:
            return {"error": "INVALID_SCAN_INPUT", "message": "no requested tools exist in the catalog."}

        city_runs = []
        opportunities = []
        errors = []

        for city in cities:
            tool_runs = []
            for tool in tools:
                try:
                    result = self.discovery_service.discover(city=city, query=tool.get("name", ""), limit=limit_per_tool)
                    if not isinstance(result, dict):
                        errors.append({"city": city, "tool_id": tool["id"], "error": "INVALID_DISCOVERY_RESULT"})
                        continue
                    tool_runs.append({
                        "tool_id": tool["id"], "tool_name": tool.get("name", ""),
                        "searched": result.get("searched", 0), "filtered": result.get("filtered", 0),
                        "selected": result.get("selected", 0), "analyzed": result.get("analyzed", 0),
                        "best_choice": result.get("best_choice"), "search_batches": result.get("search_batches", 0),
                    })
                    for item in result.get("ranking", []):
                        if isinstance(item, dict):
                            enriched = dict(item)
                            enriched.update({"city": city, "tool_id": tool["id"], "tool_name": tool.get("name", "")})
                            opportunities.append(enriched)
                except Exception as exc:
                    errors.append({"city": city, "tool_id": tool["id"], "error": type(exc).__name__})
            city_runs.append({"city": city, "tools_scanned": len(tools), "tools_completed": len(tool_runs), "tool_runs": tool_runs})

        unique = self._deduplicate(opportunities)
        ranked = self._global_rank(opportunities, limit=top_n)
        attempted = len(cities) * len(tools)
        failed = len(errors)
        return {
            "cities": cities, "cities_scanned": len(cities), "tools_scanned": len(tools),
            "opportunities": ranked["total"], "candidate_pool": len(opportunities),
            "unique_candidates": len(unique), "duplicates_removed": len(opportunities) - len(unique),
            "city_runs": city_runs, "ranking": ranked["opportunities"],
            "best_choice": ranked["best_opportunity"], "errors": errors,
            "scan_health": {
                "status": "DEGRADED" if failed else "HEALTHY",
                "attempted_tool_runs": attempted,
                "failed_tool_runs": failed,
                "successful_tool_runs": attempted - failed,
            },
        }
