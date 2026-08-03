def analyze_ad(ad_data):
    score = 100
    reasons = []

    if not ad_data.get("has_test"):
        score -= 20
        reasons.append("No testing available.")
    else:
        reasons.append("Testing available.")

    if not ad_data.get("has_warranty"):
        score -= 10
        reasons.append("No warranty.")
    else:
        reasons.append("Warranty available.")

    if ad_data.get("seller_type") == "Personal":
        score += 5
        reasons.append("Personal seller.")

    elif ad_data.get("seller_type") == "Business":
        reasons.append("Business seller.")

    if ad_data.get("condition") == "Used":
        score -= 5
        reasons.append("Used tool.")

    elif ad_data.get("condition") == "New":
        reasons.append("New tool.")

    # Keep score between 0 and 100
    score = max(0, min(100, score))

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