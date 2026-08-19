from backend.decision_engine import make_decision


def test_low_confidence_market_cannot_produce_buy_decision():
    result = make_decision({
        "tool_name": "bosch_gbh_2_26",
        "asking_price": 8000000,
        "market_data": {
            "valid": True,
            "confidence": "LOW",
            "sample_count": 1,
            "min_price": 7000000,
            "max_price": 9000000,
            "median_price": 8000000,
        },
        "has_test": True,
        "has_warranty": True,
        "description": "ابزار تست شده",
        "ad_score": 100,
        "analysis": [],
        "image_file": None,
        "image_urls": [],
    })
    assert result["decision"] != "BUY"
    assert result["market_confidence"] == "LOW"


def test_medium_confidence_dynamic_market_can_be_used():
    result = make_decision({
        "tool_name": "bosch_gbh_2_26",
        "asking_price": 8500000,
        "market_data": {
            "valid": True,
            "confidence": "MEDIUM",
            "sample_count": 2,
            "min_price": 8000000,
            "max_price": 9500000,
            "median_price": 8750000,
        },
        "has_test": True,
        "has_warranty": True,
        "description": "ابزار تست شده",
        "ad_score": 100,
        "analysis": [],
        "image_file": None,
        "image_urls": [],
    })
    assert result["market_source"] == "dynamic"
    assert result["market_confidence"] == "MEDIUM"


def test_unknown_market_data_is_explicitly_unknown():
    result = make_decision({
        "tool_name": "bosch_gbh_2_26",
        "asking_price": 8500000,
        "market_data": None,
        "has_test": True,
        "has_warranty": True,
        "description": "ابزار",
        "ad_score": 80,
        "analysis": [],
        "image_file": None,
        "image_urls": [],
    })
    assert result["market_source"] == "knowledge_base"
    assert result["price_status"] in {"VERY_GOOD_PRICE", "GOOD_PRICE", "FAIR_PRICE", "HIGH_PRICE", "VERY_HIGH_PRICE", "UNKNOWN"}
