def analyze_ad(ad_data):
    """
    Analyze advertisement quality and trust signals.
    """

    score = 100
    reasons = []

    has_test = bool(ad_data.get("has_test"))
    has_warranty = bool(ad_data.get("has_warranty"))

    seller_type = str(
        ad_data.get("seller_type", "unknown")
    ).strip().lower()

    condition = str(
        ad_data.get("condition", "unknown")
    ).strip().lower()

    # Testing
    if not has_test:
        score -= 20
        reasons.append("No testing available.")
    else:
        reasons.append("Testing available.")

    # Warranty
    if not has_warranty:
        score -= 10
        reasons.append("No warranty.")
    else:
        reasons.append("Warranty available.")

    # Seller type
    if seller_type == "personal":
        score += 5
        reasons.append("Personal seller.")

    elif seller_type == "business":
        reasons.append("Business seller.")

    # Condition
    if condition == "used":
        score -= 5
        reasons.append("Used tool.")

    elif condition == "new":
        reasons.append("New tool.")

    # Description analysis
    description = str(
        ad_data.get("description", "")
    ).lower()

    positive_words = [
        "clean",
        "low usage",
        "healthy",
        "testing available",
        "like new",
        "original",
        "well maintained"
    ]

    negative_words = [
        "repair",
        "broken",
        "fault",
        "problem",
        "burned",
        "damaged",
        "defective"
    ]

    for word in positive_words:
        if word in description:
            score += 3
            reasons.append(
                f"Positive description: {word}"
            )

    for word in negative_words:
        if word in description:
            score -= 10
            reasons.append(
                f"Risk description: {word}"
            )

    score = max(0, min(100, score))

    return {
        "tool_name": ad_data.get("tool_name"),
        "asking_price": ad_data.get("asking_price"),
        "seller_type": seller_type,
        "has_test": has_test,
        "has_warranty": has_warranty,
        "condition": condition,
        "description": description,
        "ad_score": score,
        "analysis": reasons
    }