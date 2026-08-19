import json
from pathlib import Path

from backend.tool_knowledge_builder import ToolKnowledgeBuilder
from backend.tool_candidate_promoter import ToolCandidatePromoter
from backend.divar_search_engine import DivarSearchEngine


def test_all_indexed_tools_match_knowledge_builder_schema():
    root = Path(__file__).resolve().parents[1]
    tools_dir = root / "knowledge_base" / "tools"
    index_path = tools_dir / "tools_index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    builder = ToolKnowledgeBuilder()

    assert isinstance(index.get("tools"), list)
    ids = set()
    for item in index["tools"]:
        assert item["id"] not in ids
        ids.add(item["id"])
        path = tools_dir / item["file"]
        assert path.exists(), item
        data = json.loads(path.read_text(encoding="utf-8"))
        result = builder.validate(data)
        assert result["valid"], (item["id"], result)


def test_divar_search_resolves_tool_id_to_human_query():
    engine = DivarSearchEngine()
    assert engine.build_query("makita_hr2470") == "Makita HR2470"
    assert engine.build_query("bosch_gbh_2_26", variant="DRE") == "Bosch GBH 2-26 DRE"


def test_divar_search_rejects_unknown_city_before_network_call(monkeypatch):
    engine = DivarSearchEngine()
    called = {"value": False}

    def fake_get(*args, **kwargs):
        called["value"] = True
        raise AssertionError("network must not be called")

    monkeypatch.setattr("backend.divar_search_engine.requests.get", fake_get)
    result = engine.search("UnknownCity", "makita_hr2470")
    assert result["error"] == "INVALID_SEARCH_INPUT"
    assert called["value"] is False


def test_promoter_rejects_unvalidated_candidate_without_persistence(tmp_path):
    promoter = ToolCandidatePromoter(knowledge_dir=tmp_path)
    result = promoter.promote({"status": "CANDIDATE", "brand": "Makita", "model": "HR999"})
    assert result["status"] == "REJECTED"
    assert not list(tmp_path.glob("*.json"))


def test_promoter_does_not_duplicate_existing_tool(tmp_path):
    promoter = ToolCandidatePromoter(knowledge_dir=tmp_path)
    tmp_path.joinpath("makita_hr2470.json").write_text("{}", encoding="utf-8")
    tmp_path.joinpath("tools_index.json").write_text(
        json.dumps({"tools": [{"id": "makita_hr2470", "file": "makita_hr2470.json"}]}),
        encoding="utf-8",
    )
    candidate = {
        "status": "VALIDATED",
        "brand": "Makita",
        "model": "HR2470",
        "confidence": 0.95,
        "evidence": ["marketplace evidence"],
        "market_data": {"valid": True, "sample_count": 3},
    }
    result = promoter.promote(candidate)
    assert result["status"] == "EXISTS"
