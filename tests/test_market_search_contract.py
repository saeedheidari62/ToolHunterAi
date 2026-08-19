from backend.divar_search_engine import DivarSearchEngine


def test_build_query_resolves_tool_id_to_catalog_name():
    engine = DivarSearchEngine()
    assert engine.build_query("makita_hr2470") == "Makita HR2470"


def test_build_query_preserves_variant():
    engine = DivarSearchEngine()
    assert engine.build_query("bosch_gbh_2_26", "DRE") == "Bosch GBH 2-26 DRE"


def test_invalid_city_does_not_search():
    engine = DivarSearchEngine()
    result = engine.search("", "makita_hr2470")
    assert result["error"] == "INVALID_SEARCH_INPUT"
    assert result["results"] == []
