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
    """Analyze asking price against the strongest trustworthy market benchmark."""
    market = tool_data.get("market", {})
    if not isinstance(market, dict):
        market = {}

    dynamic_confidence = market_data.get("confidence") if isinstance(market_data, dict) else None
    dynamic_confidence_level = _normalize_market_confidence(dynamic_confidence)

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
        and dynamic_confidence_level in ("HIGH", "MEDIUM")
        and dynamic_sample_count >= 2
        and dynamic_range_valid
    )

    if use_dynamic_market:
        benchmark = {
            "used_price_min": dynamic_min,
            "used_price_max": dynamic_max,
            "median_price": dynamic_median,
        }
        market_source = "dynamic"
        market_confidence = dynamic_confidence_level
        benchmark_reason = "Dynamic market data passed the confidence, sample-count, and range checks."
    else:
        benchmark = market
        market_source = "knowledge_base"
        market_confidence = _normalize_market_confidence(
            market.get("price_confidence", market.get("confidence"))
        )
        if not market_confidence:
            market_confidence = "NONE"
        benchmark_reason = "Knowledge Base market data was used because dynamic market data was unavailable or insufficient."

    low = benchmark.get("used_price_min")
    high = benchmark.get("used_price_max")
    if low is None:
        low = benchmark.get("median_price")
    if high is None:
        high = benchmark.get("median_price")

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
            "market_confidence": market_confidence,
            "market_benchmark_reason": benchmark_reason,
        }

    if asking_price <= 0 or low <= 0 or high <= 0 or low > high:
        return {
            "price_score": 50,
            "price_status": "UNKNOWN",
            "price_reason": ["Invalid market price data."],
            "price_difference_percent": None,
            "market_source": market_source,
            "market_confidence": market_confidence,
            "market_benchmark_reason": benchmark_reason,
        }

    market_reference = benchmark.get("median_price")
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
            "market_confidence": market_confidence,
            "market_benchmark_reason": benchmark_reason,
        }

    difference_percent = ((asking_price - market_reference) / market_reference) * 100
    reasons = [benchmark_reason]

    if isinstance(market_data, dict) and market_data.get("valid") and not use_dynamic_market:
        if dynamic_confidence_level == "LOW":
            reasons.append("Dynamic market confidence is LOW; the static baseline was used.")
        elif dynamic_sample_count < 2:
            reasons.append("Dynamic market data has fewer than 2 effective samples; the static baseline was used.")
        else:
            reasons.append("Dynamic market data did not meet the minimum trust requirements, so the static baseline was used.")

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
        "market_confidence": market_confidence,
        "market_benchmark_reason": benchmark_reason,
    }
