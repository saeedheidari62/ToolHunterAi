def analyze_price(
    tool_data,
    asking_price,
    market_data=None
):
    """
    Analyze asking price against the tool's used-market range.

    If valid market_data is provided, it takes priority
    over the static Knowledge Base market range.

    Expected Knowledge Base format:

    market:
        used_price_min
        used_price_max
    """

    market = tool_data.get("market", {})

    # Prefer dynamic market data when available.
    if (
        isinstance(market_data, dict)
        and market_data.get("valid")
    ):
        market = {
            "used_price_min": market_data.get("min_price"),
            "used_price_max": market_data.get("max_price")
        }

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
            "price_reason": [
                "No valid market price data is available."
            ],
            "price_difference_percent": None
        }

    if (
        asking_price <= 0
        or low <= 0
        or high <= 0
        or low > high
    ):
        return {
            "price_score": 50,
            "price_status": "UNKNOWN",
            "price_reason": [
                "Invalid market price data."
            ],
            "price_difference_percent": None
        }

    average = (low + high) / 2

    difference_percent = (
        (asking_price - average)
        / average
    ) * 100

    reasons = []

    if asking_price < low * 0.90:

        score = 80
        status = "VERY_GOOD_PRICE"

        reasons.append(
            "The unusually low price should be verified carefully."
        )

    elif asking_price < low:

        score = 92
        status = "VERY_GOOD_PRICE"

        reasons.append(
            "Price is below the normal market range."
        )

    elif asking_price <= low + (average - low) * 0.25:

        score = 95
        status = "VERY_GOOD_PRICE"

        reasons.append(
            "Price is near the low end of the market range."
        )

    elif asking_price <= average:

        score = 88
        status = "GOOD_PRICE"

        reasons.append(
            "Price is below the market average."
        )

    elif asking_price < high - (high - average) * 0.25:

        score = 78
        status = "FAIR_PRICE"

        reasons.append(
            "Price is above the market average but within a reasonable range."
        )

    elif asking_price <= high:

        score = 65
        status = "HIGH_PRICE"

        reasons.append(
            "Price is near the high end of the market range."
        )

    elif asking_price <= high * 1.10:

        score = 45
        status = "HIGH_PRICE"

        reasons.append(
            "Price is above the normal market range."
        )

    else:

        score = 20
        status = "VERY_HIGH_PRICE"

        reasons.append(
            "Price is significantly higher than the market range."
        )

    return {
        "price_score": round(score),
        "price_status": status,
        "price_reason": reasons,
        "price_difference_percent": round(
            difference_percent,
            2
        )
    }