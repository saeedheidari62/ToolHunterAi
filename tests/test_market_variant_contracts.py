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
