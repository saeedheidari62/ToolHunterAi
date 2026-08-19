from backend.divar_search_engine import DivarSearchEngine


def test_build_query_resolves_tool_id_to_catalog_name():
    engine = DivarSearchEngine()
    assert engine.build_query("makita_hr2470") == "Makita HR2470"


def test_build_query_preserves_variant():
    engine = DivarSearchEngine()
    assert engine.build_query("bosch_gbh_2_26", "DRE") == "Bosch GBH 2-26 DRE"


def test_persian_city_resolves_to_divar_slug():
    engine = DivarSearchEngine()
    assert engine._normalize_city("تهران") == "tehran"
    assert engine._normalize_city("کرج") == "karaj"


def test_invalid_city_does_not_search():
    engine = DivarSearchEngine()
    result = engine.search("شهر-ناشناخته", "makita_hr2470")
    assert result["error"] == "INVALID_SEARCH_INPUT"
    assert result["results"] == []


def test_variant_filter_handles_non_bosch_variants():
    engine = DivarSearchEngine()
    results = [
        {"title": "Makita HR2470 DRE", "price": 10000000},
        {"title": "Makita HR2470", "price": 9000000},
    ]
    filtered = engine.filter_results(results, "makita_hr2470", "DRE")
    assert len(filtered) == 1
    assert "DRE" in filtered[0]["title"]
