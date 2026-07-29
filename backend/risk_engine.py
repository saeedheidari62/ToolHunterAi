def calculate_risk(tool_data, ad_data):
    risk = tool_data["risk"]["score"]

    if not ad_data.get("has_test"):
        risk += 15

    if not ad_data.get("has_warranty"):
        risk += 5

    if ad_data.get("condition") == "Used":
        risk += 5

    risk = max(0, min(risk, 100))

    if risk <= 30:
        level = "LOW"
    elif risk <= 60:
        level = "MEDIUM"
    else:
        level = "HIGH"

    return {
        "score": risk,
        "level": level
    }