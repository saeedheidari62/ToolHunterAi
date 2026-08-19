import json
from pathlib import Path

from backend.divar_search_engine import DivarSearchEngine
from backend.price_analyzer import analyze_price

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "knowledge_base" / "tools" / "tools_index.json"
TOOLS_DIR = ROOT / "knowledge_base" / "tools"


def test_all_tool_index_entries_resolve_to_catalog_names():
    payload = json.loads(INDEX.read_text(encoding="utf-8"))
    engine = DivarSearchEngine()
    ids = [item["id"] for item in payload["tools"]]
    assert len(ids) == len(set(ids))
    for item in payload["tools"]:
        assert Path(item["file"]).name in {p.name for p in TOOLS_DIR.glob("*.json")}
        assert engine.build_query(item["id"]) == item["name"]


def test_aliases_resolve_to_human_market_query():
    engine = DivarSearchEngine()
    assert engine.build_query("hr2470") == "Makita HR2470"
    assert engine.build_query("بوش ۲۶") == "Bosch GBH 2-26"


def test_dynamic_market_only_when_confidence_is_reliable():
    tool = {"market": {"used_price_min": 8_000_000, "used_price_max": 9_500_000}}
    low = analyze_price(tool, 9_000_000, {"valid": True, "confidence": "LOW", "min_price": 20_000_000, "max_price": 20_000_000, "median_price": 20_000_000})
    assert low["market_source"] == "knowledge_base"
    high = analyze_price(tool, 9_000_000, {"valid": True, "confidence": "HIGH", "min_price": 8_000_000, "max_price": 9_500_000, "median_price": 8_750_000})
    assert high["market_source"] == "dynamic"
