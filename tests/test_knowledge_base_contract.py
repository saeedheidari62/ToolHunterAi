import json
from pathlib import Path

from backend.tool_knowledge_builder import ToolKnowledgeBuilder


def test_all_indexed_tools_match_knowledge_schema():
    base = Path(__file__).resolve().parent.parent / "knowledge_base" / "tools"
    index = json.loads((base / "tools_index.json").read_text(encoding="utf-8"))
    builder = ToolKnowledgeBuilder()

    failures = []
    for entry in index.get("tools", []):
        tool_id = entry["id"]
        path = base / entry["file"]
        if not path.exists():
            failures.append(f"{tool_id}: missing file {entry['file']}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        result = builder.validate(data)
        if not result["valid"]:
            failures.append(f"{tool_id}: {result['errors']}")

    assert not failures, "Knowledge Base schema failures: " + " | ".join(failures)


def test_unavailable_market_is_explicit_not_fake():
    builder = ToolKnowledgeBuilder()
    data = {
        "tool_name": "Legacy Tool",
        "category": "toolbox",
        "brand": "Legacy",
        "aliases": ["legacy"],
        "technical": {},
        "common_failures": [],
        "inspection": [],
        "repair": {},
        "risk": {},
        "market": {
            "used_price_min": 0,
            "used_price_max": 0,
            "median_price": None,
            "sample_count": 0,
            "price_confidence": 0.0,
            "sources": [],
            "status": "unavailable",
        },
        "confidence": "legacy_static",
        "sources": [],
    }
    assert builder.validate(data)["valid"] is True
