def analyze_ad(ad_data):
    return {
        "tool_name": ad_data.get("tool_name"),
        "asking_price": ad_data.get("asking_price"),
        "seller_type": ad_data.get("seller_type", "Unknown"),
        "has_test": ad_data.get("has_test", False),
        "has_warranty": ad_data.get("has_warranty", False),
        "condition": ad_data.get("condition", "Unknown"),
        "description_score": 0,
        "image_score": 0
    }