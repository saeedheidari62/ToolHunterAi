def analyze_price(tool_data, asking_price, market_data=None):
    """Analyze asking price against the best available market benchmark."""
    market = tool_data.get("market", {})

    dynamic_confidence = (
        market_data.get("confidence")
        if isinstance(market_data, dict)
        else None
    )
    use_dynamic_market = (
        isinstance(market_data, dict)
        and market_data.get("valid")
        and dynamic_confidence in ("HIGH", "MEDIUM")
    )

    if use_dynamic_market:
        market = {
            "used_price_min": market_data.get("min_price"),
            "used_price_max": market_data.get("max_price"),
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

    market_reference = (
        market_data.get("median_price")
        if use_dynamic_market and market_data.get("median_price") is not None
        else (low + high) / 2
    )

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

    if isinstance(market_data, dict) and market_data.get("valid") and dynamic_confidence == "LOW":
        reasons.append("Dynamic market data had LOW confidence, so the static market baseline was used.")

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
    }
