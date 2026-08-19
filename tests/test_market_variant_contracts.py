from backend.divar_search_engine import DivarSearchEngine
from backend.market_price_engine import MarketPriceEngine
from backend.tool_variant_matcher import ToolVariantMatcher


def test_market_confidence_is_based_on_effective_samples():
    engine = MarketPriceEngine()
    assert engine.calculate([100, 110, 120])["confidence"] == "HIGH"
    assert engine.calculate([100, 110])["confidence"] == "MEDIUM"
    assert engine.calculate([100])["confidence"] == "LOW"
    assert engine.calculate([])["confidence"] == "NONE"


def test_variant_matcher_normalizes_persian_digits_and_spacing():
    matcher = ToolVariantMatcher()
    assert matcher.detect("Bosch GBH 2-26 DFR", "bosch_gbh_2_26") == "DFR"
    assert matcher.detect("بوش GBH ۲ ۲۶ DRE", "bosch_gbh_2_26") == "DRE"
    assert matcher.detect("GBH 2 26", "bosch_gbh_2_26") == "BASE"


def test_divar_search_resolves_tool_ids_to_display_names():
    engine = DivarSearchEngine()
    assert engine.build_query("makita_hr2470") == "Makita HR2470"
    assert engine.build_query("bosch_gsh500") == "Bosch GSH500"


def test_divar_search_applies_variant_to_human_query():
    engine = DivarSearchEngine()
    assert engine.build_query("bosch_gbh_2_26", "DFR") == "Bosch GBH 2-26 DFR"


def test_divar_search_rejects_missing_city_or_query():
    engine = DivarSearchEngine()
    result = engine.search("", "makita_hr2470")
    assert result["error"] == "INVALID_SEARCH_INPUT"


def test_divar_parser_keeps_only_divar_listing_links():
    engine = DivarSearchEngine()
    html = '''
    <html><body>
      <a href="/v/abc">ابزار 1</a>
      <a href="/about">درباره دیوار</a>
      <a href="/v/abc?foo=1">ابزار 1</a>
    </body></html>
    '''
    result = engine.parse_results(html)
    assert len(result["results"]) == 1
    assert result["results"][0]["url"] == "https://divar.ir/v/abc"
