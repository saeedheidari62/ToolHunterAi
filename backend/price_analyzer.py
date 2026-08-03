def analyze_price(tool_data, asking_price):
    """
    Compare asking price with market prices
    """

    reasons = []

    market_prices = tool_data.get("market_prices", {})

    low = market_prices.get("low")
    average = market_prices.get("average")
    high = market_prices.get("high")

    if not low or not average or not high:
        return {
            "price_score": 50,
            "price_status": "Unknown",
            "price_reason": "No market price data available."
        }


    if asking_price <= low:
        score = 100
        status = "Excellent"
        reasons.append("Price is below market range.")

    elif asking_price <= average:
        score = 85
        status = "Good"
        reasons.append("Price is acceptable compared to market.")

    elif asking_price <= high:
        score = 60
        status = "High"
        reasons.append("Price is above average market price.")

    else:
        score = 30
        status = "Very High"
        reasons.append("Price is higher than market range.")


    return {
        "price_score": score,
        "price_status": status,
        "price_reason": reasons
    }