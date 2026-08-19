def _normalize_market_confidence(value):
    if isinstance(value, str):
        text = value.strip().upper()
        if text in {"HIGH", "MEDIUM", "LOW", "NONE"}:
            return text
        try:
            value = float(text)
        except (TypeError, ValueError):
            return None

    try:
        score = float(value)
    except (TypeError, ValueError):
        return None

    if score >= 0.8:
        return "HIGH"
    if score >= 0.6:
        return "MEDIUM"
    if score > 0:
        return "LOW"
    return "NONE"


def analyze_price(tool_data, asking_price, market_data=None):
    """Analyze asking price against the best available market benchmark."""
    market = tool_data.get("market", {})

    dynamic_confidence = (
        market_data.get("confidence")
        if isinstance(market_data, dict)
        else None
    )
    confidence_level = _normalize_market_confidence(dynamic_confidence)
    dynamic_sample_count = 0
    try:
        dynamic_sample_count = int(market_data.get("sample_count", 0)) if isinstance(market_data, dict) else 0
    except (TypeError, ValueError):
        dynamic_sample_count = 0

    dynamic_min = market_data.get("min_price") if isinstance(market_data, dict) else None
    dynamic_max = market_data.get("max_price") if isinstance(market_data, dict) else None
    dynamic_median = market_data.get("median_price") if isinstance(market_data, dict) else None
    dynamic_range_valid = all(
        isinstance(value, (int, float)) and float(value) > 0
        for value in (dynamic_min, dynamic_max, dynamic_median)
    ) and float(dynamic_min) <= float(dynamic_median) <= float(dynamic_max)

    use_dynamic_market = (
        isinstance(market_data, dict)
        and market_data.get("valid")
        and confidence_level in ("HIGH", "MEDIUM")
        and dynamic_sample_count >= 2
        and dynamic_range_valid
    )

    if use_dynamic_market:
        market = {
            "used_price_min": dynamic_min,
            "used_price_max": dynamic_max,
        }
        market_source = "dynamic"
    else:
        market_source = "knowledge_base"

    low = market.get("used_price_min")
    high = market.get("used_price_max")

    try:
        asking_price = float(asking_price)
        low = float(low)
        high = float(high)
    except (TypeError, ValueError):
        return {
            "price_score": 50,
            "price_status": "UNKNOWN",
            "price_reason": ["No valid market price data is available."],
            "price_difference_percent": None,
            "market_source": market_source,
        }

    if asking_price <= 0 or low <= 0 or high <= 0 or low > high:
        return {
            "price_score": 50,
            "price_status": "UNKNOWN",
            "price_reason": ["Invalid market price data."],
            "price_difference_percent": None,
            "market_source": market_source,
        }

    market_reference = dynamic_median if use_dynamic_market and dynamic_median is not None else (low + high) / 2

    try:
        market_reference = float(market_reference)
    except (TypeError, ValueError):
        market_reference = (low + high) / 2

    if market_reference <= 0:
        return {
            "price_score": 50,
            "price_status": "UNKNOWN",
            "price_reason": ["Invalid market reference price."],
            "price_difference_percent": None,
            "market_source": market_source,
        }

    difference_percent = ((asking_price - market_reference) / market_reference) * 100
    reasons = []

    if isinstance(market_data, dict) and market_data.get("valid") and (
        confidence_level == "LOW" or dynamic_sample_count < 2 or not dynamic_range_valid
    ):
        reasons.append("Dynamic market data was not strong enough, so the static market baseline was used.")

    if asking_price < low * 0.90:
        score, status = 80, "VERY_GOOD_PRICE"
        reasons.append("The unusually low price should be verified carefully.")
    elif asking_price < low:
        score, status = 92, "VERY_GOOD_PRICE"
        reasons.append("Price is below the normal market range.")
    elif asking_price <= low + (market_reference - low) * 0.25:
        score, status = 95, "VERY_GOOD_PRICE"
        reasons.append("Price is near the low end of the market range.")
    elif asking_price <= market_reference:
        score, status = 88, "GOOD_PRICE"
        reasons.append("Price is below the market average.")
    elif asking_price < high - (high - market_reference) * 0.25:
        score, status = 78, "FAIR_PRICE"
        reasons.append("Price is above the market average but within a reasonable range.")
    elif asking_price <= high:
        score, status = 65, "HIGH_PRICE"
        reasons.append("Price is near the high end of the market range.")
    elif asking_price <= high * 1.10:
        score, status = 45, "HIGH_PRICE"
        reasons.append("Price is above the normal market range.")
    else:
        score, status = 20, "VERY_HIGH_PRICE"
        reasons.append("Price is significantly higher than the market range.")

    return {
        "price_score": round(score),
        "price_status": status,
        "price_reason": reasons,
        "price_difference_percent": round(difference_percent, 2),
        "market_source": market_source,
        "market_confidence": confidence_level,
    }
