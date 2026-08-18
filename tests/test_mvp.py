from backend.api import analyze_single_ad
from backend.price_analyzer import analyze_price
from backend.tool_variant_matcher import ToolVariantMatcher


def run_case(name, ad, expected_tool=None, expected_error=None):
    result = analyze_single_ad(ad)

    if expected_error:
        assert result.get("error") == expected_error, (name, result)
        return

    assert "error" not in result, (name, result)
    assert result.get("tool") == expected_tool, (name, result)
    assert result.get("decision") in {"BUY", "REVIEW", "DON'T BUY"}, (name, result)
    assert 0 <= result.get("buy_score", -1) <= 100, (name, result)
    assert 0 <= result.get("risk_score", -1) <= 100, (name, result)
    assert result.get("decision_reason"), (name, result)
    assert result.get("next_action"), (name, result)


def test_bosch_gbh_2_26():
    run_case(
        "Bosch GBH 2-26",
        {
            "title": "Bosch GBH 2-26",
            "description": "دریل بتن کن بوش GBH 2-26 سالم با امکان تست",
            "price": 8500000,
            "seller_type": "personal",
            "testing": True,
            "warranty": False,
            "condition": "used"
        },
        "bosch_gbh_2_26"
    )


def test_bosch_gsh500():
    run_case(
        "Bosch GSH500",
        {
            "title": "Bosch GSH500",
            "description": "بتن کن بوش مدل GSH500 سالم",
            "price": 9000000,
            "seller_type": "personal",
            "testing": False,
            "warranty": False,
            "condition": "used"
        },
        "bosch_gsh500"
    )


def test_makita_hr2470():
    run_case(
        "Makita HR2470",
        {
            "title": "Makita HR2470",
            "description": "بتن کن ماکیتا 2470 سالم",
            "price": 8000000,
            "seller_type": "personal",
            "testing": True,
            "warranty": False,
            "condition": "used"
        },
        "makita_hr2470"
    )


def test_variant_detection():
    matcher = ToolVariantMatcher()
    tool_id = "bosch_gbh_2_26"

    assert matcher.detect("Bosch GBH 2-26 DRE Professional", tool_id) == "DRE"
    assert matcher.detect("بتن کن بوش GBH 2-26 DFR", tool_id) == "DFR"
    assert matcher.detect("دریل بوش GBH 2-26 در حد نو", tool_id) == "BASE"


def test_low_confidence_market_fallback():
    tool = {
        "market": {
            "used_price_min": 8000000,
            "used_price_max": 9500000
        }
    }

    result = analyze_price(
        tool,
        9000000,
        market_data={
            "valid": True,
            "sample_count": 1,
            "min_price": 27500000,
            "max_price": 27500000,
            "median_price": 27500000,
            "confidence": "LOW"
        }
    )

    assert result["price_status"] == "GOOD_PRICE", result
    assert result["price_difference_percent"] == 0.0, result
    assert any("LOW confidence" in reason for reason in result["price_reason"]), result


def test_medium_confidence_dynamic_market():
    tool = {
        "market": {
            "used_price_min": 8000000,
            "used_price_max": 9500000
        }
    }

    result = analyze_price(
        tool,
        14900000,
        market_data={
            "valid": True,
            "sample_count": 2,
            "min_price": 12000000,
            "max_price": 14900000,
            "median_price": 13450000,
            "confidence": "MEDIUM"
        }
    )

    assert result["price_status"] == "HIGH_PRICE", result
    assert result["price_difference_percent"] == 10.78, result
    assert not any("LOW confidence" in reason for reason in result["price_reason"]), result


def test_decision_boundaries(monkeypatch):
    from backend import decision_engine

    monkeypatch.setattr(
        decision_engine,
        "load_tool",
        lambda _: {
            "risk": {"score": 0},
            "buy_score": 100,
            "market": {
                "used_price_min": 100,
                "used_price_max": 100
            }
        }
    )
    monkeypatch.setattr(
        decision_engine,
        "analyze_description",
        lambda _: {
            "description_risk": 0,
            "description_reasons": [],
            "price_signal": "NONE"
        }
    )
    monkeypatch.setattr(
        decision_engine.image_downloader,
        "download",
        lambda _: []
    )
    monkeypatch.setattr(
        decision_engine,
        "analyze_image",
        lambda _: {"image_risk": 0, "image_reasons": []}
    )
    monkeypatch.setattr(
        decision_engine,
        "analyze_price",
        lambda *_args, **_kwargs: {
            "price_status": "GOOD_PRICE",
            "price_score": 50,
            "price_difference_percent": 0,
            "price_reason": []
        }
    )

    base = {
        "tool_name": "bosch_gbh_2_26",
        "asking_price": 100,
        "has_test": True,
        "has_warranty": False,
        "description": "",
        "ad_score": 50,
        "analysis": []
    }

    result = decision_engine.make_decision(base)
    assert result["decision"] == "BUY", result

    review_data = dict(base)
    review_data["ad_score"] = 50
    monkeypatch.setattr(
        decision_engine,
        "load_tool",
        lambda _: {
            "risk": {"score": 20},
            "buy_score": 75,
            "market": {
                "used_price_min": 100,
                "used_price_max": 100
            }
        }
    )
    result = decision_engine.make_decision(review_data)
    assert result["decision"] == "REVIEW", result

    reject_data = dict(base)
    reject_data["has_test"] = False
    reject_data["has_warranty"] = True
    monkeypatch.setattr(
        decision_engine,
        "load_tool",
        lambda _: {
            "risk": {"score": 80},
            "buy_score": 50,
            "market": {
                "used_price_min": 100,
                "used_price_max": 100
            }
        }
    )
    result = decision_engine.make_decision(reject_data)
    assert result["decision"] == "DON'T BUY", result


def test_end_to_end_dre_dynamic_market(monkeypatch):
    from backend import api

    monkeypatch.setattr(
        api,
        "get_dynamic_market_data",
        lambda *_args, **_kwargs: {
            "valid": True,
            "sample_count": 2,
            "min_price": 12000000.0,
            "max_price": 14900000.0,
            "median_price": 13450000.0,
            "confidence": "MEDIUM",
            "variant": "DRE"
        }
    )

    result = analyze_single_ad({
        "title": "دریل بتن‌کن بوش آلمانی GBH 2-26 DRE Professional",
        "description": "دریل بتن کن بوش GBH 2-26 DRE در حد نو",
        "price": 14900000,
        "seller_type": "shop",
        "testing": True,
        "warranty": False,
        "condition": "used"
    })

    assert result["tool"] == "bosch_gbh_2_26", result
    assert result["variant"] == "DRE", result
    assert result["market_data"]["confidence"] == "MEDIUM", result
    assert result["market_data"]["median_price"] == 13450000.0, result
    assert result["price_status"] == "HIGH_PRICE", result
    assert result["price_difference_percent"] == 10.78, result
    assert result["decision"] in {"BUY", "REVIEW", "DON'T BUY"}, result
    assert result.get("decision_reason"), result
    assert result.get("next_action"), result


def test_end_to_end_dfr_low_confidence_fallback(monkeypatch):
    from backend import api

    monkeypatch.setattr(
        api,
        "get_dynamic_market_data",
        lambda *_args, **_kwargs: {
            "valid": True,
            "sample_count": 1,
            "min_price": 27500000.0,
            "max_price": 27500000.0,
            "median_price": 27500000.0,
            "confidence": "LOW",
            "variant": "DFR"
        }
    )

    result = analyze_single_ad({
        "title": "بتن کن بوش GBH 2-26 DFR",
        "description": "بتن کن بوش GBH 2-26 DFR سالم",
        "price": 27500000,
        "seller_type": "personal",
        "testing": False,
        "warranty": False,
        "condition": "used"
    })

    assert result["tool"] == "bosch_gbh_2_26", result
    assert result["variant"] == "DFR", result
    assert result["market_data"]["confidence"] == "LOW", result
    assert result["price_status"] == "VERY_HIGH_PRICE", result
    assert result["price_difference_percent"] == 214.29, result
    assert result["decision"] == "REVIEW", result
    assert any(
        "LOW confidence" in reason
        for reason in result.get("reasons", [])
    ), result
    assert result.get("decision_reason"), result
    assert result.get("next_action"), result
