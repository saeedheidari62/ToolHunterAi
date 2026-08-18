from backend.tool_variant_matcher import ToolVariantMatcher
from backend.divar_search_engine import DivarSearchEngine
from backend.price_analyzer import analyze_price


TOOL = {
    "market": {
        "used_price_min": 8_000_000,
        "used_price_max": 9_500_000,
    }
}


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def test_variant_matching():
    matcher = ToolVariantMatcher()
    tool_id = "bosch_gbh_2_26"

    check(
        "DFR variant detection",
        matcher.detect("بتن کن بوش GBH 2-26 DFR", tool_id) == "DFR",
    )
    check(
        "DRE variant detection",
        matcher.detect("Bosch GBH 2-26 DRE Professional", tool_id) == "DRE",
    )
    check(
        "BASE variant detection",
        matcher.detect("دریل بوش GBH 2-26 در حد نو", tool_id) == "BASE",
    )


def test_variant_filtering():
    engine = DivarSearchEngine()
    results = [
        {"title": "بتن کن بوش GBH 2-26 DFR در حد نو", "price": 27_500_000},
        {"title": "دریل بوش GBH 2-26 DRE در حد نو", "price": 12_000_000},
        {"title": "دریل بوش GBH 2-26 DRE Professional", "price": 14_900_000},
        {"title": "GBH 2-26 DFR بدون قیمت", "price": None},
    ]

    dfr = engine.filter_results(results, "bosch_gbh_2_26", "DFR")
    dre = engine.filter_results(results, "bosch_gbh_2_26", "DRE")

    check("DFR filtering", len(dfr) == 1 and dfr[0]["price"] == 27_500_000)
    check("DRE filtering", len(dre) == 2)


def test_low_confidence_fallback():
    low_confidence = {
        "valid": True,
        "sample_count": 1,
        "min_price": 27_500_000,
        "max_price": 27_500_000,
        "median_price": 27_500_000,
        "confidence": "LOW",
        "variant": "DFR",
    }

    result = analyze_price(TOOL, 9_000_000, low_confidence)

    check("LOW confidence uses static baseline", result["price_difference_percent"] == 2.86)
    check("LOW confidence produces explainable reason", any("LOW confidence" in r for r in result["price_reason"]))


def test_medium_confidence_dynamic_market():
    medium_confidence = {
        "valid": True,
        "sample_count": 2,
        "min_price": 12_000_000,
        "max_price": 14_900_000,
        "median_price": 13_450_000,
        "confidence": "MEDIUM",
        "variant": "DRE",
    }

    result = analyze_price(TOOL, 14_900_000, medium_confidence)

    check("MEDIUM confidence uses dynamic range", result["price_status"] == "HIGH_PRICE")
    check("MEDIUM confidence uses dynamic median", result["price_difference_percent"] == 10.78)


def main():
    print("===== TOOLHUNTERAI REGRESSION TESTS =====")
    test_variant_matching()
    test_variant_filtering()
    test_low_confidence_fallback()
    test_medium_confidence_dynamic_market()
    print("===== ALL REGRESSION TESTS PASSED =====")


if __name__ == "__main__":
    main()
