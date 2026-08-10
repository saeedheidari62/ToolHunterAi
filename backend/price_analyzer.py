def analyze_price(tool_data, asking_price):
    """
    Analyze asking price against the tool's market price range.

    Expected knowledge base format:

    market:
        used_price_min
        used_price_max
    """

    market = tool_data.get("market", {})

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

    # More than 10% below minimum:
    # attractive but potentially suspicious.
    if asking_price < low * 0.90:

        score = 80
        status = "VERY_GOOD_PRICE"

        reasons.append(
            "Price is significantly below the normal market range."
        )

        reasons.append(
            "The unusually low price should be verified carefully."
        )

    # Between 90% of minimum and minimum.
    elif asking_price <= low:

        score = 95
        status = "VERY_GOOD_PRICE"

        reasons.append(
            "Price is at the low end of the market range."
        )

    # Below market average.
    elif asking_price <= average:

        score = 88
        status = "GOOD_PRICE"

        reasons.append(
            "Price is below the market average."
        )

    # Above average but still inside normal range.
    elif asking_price <= high:

        score = 72
        status = "FAIR_PRICE"

        reasons.append(
            "Price is within the normal market range."
        )

    # Up to 10% above maximum.
    elif asking_price <= high * 1.10:

        score = 45
        status = "HIGH_PRICE"

        reasons.append(
            "Price is above the normal market range."
        )

    # More than 10% above maximum.
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