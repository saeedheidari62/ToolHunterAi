from backend.divar_search_engine import DivarSearchEngine


def test_build_query_uses_catalog_name_for_tool_id():
    engine = DivarSearchEngine()
    assert engine.build_query("makita_hr2470") == "Makita HR2470"
    assert engine.build_query("bosch_gbh_2_26", "DRE") == "Bosch GBH 2-26 DRE"


def test_build_query_accepts_alias():
    engine = DivarSearchEngine()
    assert engine.build_query("hr2470") == "Makita HR2470"
    assert engine.build_query("بوش ۲۶") == "Bosch GBH 2-26"


def test_filter_results_normalizes_persian_digits_and_variant():
    engine = DivarSearchEngine()
    results = [
        {"title": "بتن کن بوش GBH ۲-۲۶ DRE", "price": 12000000},
        {"title": "بتن کن بوش GBH 2-26 DFR", "price": 13000000},
        {"title": "بتن کن بوش GBH 2-26 DRE", "price": None},
    ]
    filtered = engine.filter_results(results, "bosch_gbh_2_26", "DRE")
    assert len(filtered) == 1
    assert filtered[0]["price"] == 12000000


def test_invalid_search_input_is_structured():
    engine = DivarSearchEngine()
    assert engine.search("", "makita_hr2470")["error"] == "INVALID_SEARCH_INPUT"
    assert engine.search("tehran", "")["error"] == "INVALID_SEARCH_INPUT"
