import importlib
from pathlib import Path


def test_backend_modules_import_without_secret():
    modules = [
        "backend.api",
        "backend.app",
        "backend.collector",
        "backend.ad_normalizer",
        "backend.diwar_fetcher",
        "backend.diwar_collector",
        "backend.divar_search_engine",
        "backend.market_price_engine",
        "backend.decision_engine",
        "backend.tool_matcher",
        "backend.tool_variant_matcher",
        "backend.evidence_layer",
        "backend.technical_intelligence_collector",
        "backend.tool_knowledge_builder",
        "backend.ai.tool_discovery",
        "backend.ai.tool_candidate_validator",
        "backend.ai.tool_candidate_promoter",
        "backend.ai.tool_resolver",
    ]

    for module_name in modules:
        importlib.import_module(module_name)


def test_all_knowledge_base_tools_are_json_objects():
    tools_dir = Path(__file__).resolve().parents[1] / "knowledge_base" / "tools"
    tool_files = sorted(
        path for path in tools_dir.glob("*.json") if path.name != "tools_index.json"
    )

    assert tool_files

    import json

    for path in tool_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict), path.name
        assert data.get("id"), path.name
        assert data.get("name"), path.name


def test_main_workflow_does_not_require_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from backend.api import analyze_single_ad

    result = analyze_single_ad({
        "title": "Bosch GBH 2-26",
        "description": "Bosch original used tool",
        "price": 8500000,
        "seller_type": "personal",
        "testing": True,
        "warranty": False,
        "condition": "used",
    })

    assert isinstance(result, dict)
    assert "error" not in result or result["error"] != "OPENAI_API_KEY_MISSING"
