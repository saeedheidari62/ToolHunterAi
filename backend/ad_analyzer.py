def analyze_ad(ad_data):
    score = 100
    reasons = []

    if not ad_data.get("has_test"):
        score -= 20
        reasons.append("No testing available.")

    if not ad_data.get("has_warranty"):
        score -= 10
        reasons.append("No warranty.")

    if ad_data.get("seller_type") == "Personal":
        score += 5
        reasons.append("Personal seller.")

    if ad_data.get("condition") == "Used":
        score -= 5
        reasons.append("Used tool.")

    return {
        "tool_name": ad_data.get("tool_name"),
        "asking_price": ad_data.get("asking_price"),
        "seller_type": ad_data.get("seller_type"),
        "has_test": ad_data.get("has_test"),
        "has_warranty": ad_data.get("has_warranty"),
        "condition": ad_data.get("condition"),
        "ad_score": score,
        "analysis": reasons
    }