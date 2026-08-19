from backend.divar_search_engine import DivarSearchEngine

def test_persian_city_normalization():
    engine = DivarSearchEngine()
    assert engine._normalize_city("تهران") == "tehran"
    assert engine._normalize_city("کرج") == "karaj"

def test_unknown_city_rejected():
    engine = DivarSearchEngine()
    result = engine.search("شهر_ناشناخته", "Bosch GBH 2-26")
    assert result["error"] == "INVALID_SEARCH_INPUT"

def test_index_refreshes_after_promotion(tmp_path):
    import json
    engine = DivarSearchEngine()
    path = tmp_path / "tools_index.json"
    engine.tools_index_path = path
    path.write_text(json.dumps({"tools":[{"id":"new_tool","name":"Old Name","aliases":[]}]}, ensure_ascii=False), encoding="utf-8")
    assert engine.build_query("new_tool") == "Old Name"
    path.write_text(json.dumps({"tools":[{"id":"new_tool","name":"New Name","aliases":[]}]}, ensure_ascii=False), encoding="utf-8")
    assert engine.build_query("new_tool") == "New Name"
