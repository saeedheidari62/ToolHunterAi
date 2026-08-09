import json
from pathlib import Path
from description_analyzer import analyze_description


def load_tool(tool_name):
    base_path = Path(__file__).resolve().parent.parent
    file_path = base_path / "knowledge_base" / "tools" / f"{tool_name}.json"

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def make_decision(ad_data):

    tool_name = ad_data["tool_name"]
    tool = load_tool(tool_name)

    risk_score = tool["risk"]["score"]
    base_buy_score = tool["buy_score"]

    ad_score = ad_data.get("ad_score", 50)

    buy_score = (base_buy_score * 0.8) + (ad_score * 0.2)

    reasons = []

    # Structured decision data
    has_test = bool(ad_data.get("has_test"))
    has_warranty = bool(ad_data.get("has_warranty"))
    price_status = "unknown"

    # Ad analysis reasons
    reasons.extend(ad_data.get("analysis", []))

    # Description analysis
    description = ad_data.get("description", "")

    description_result = analyze_description(description)

    risk_score += description_result["description_risk"]

    reasons.extend(
        description_result["description_reasons"]
    )

    # Price analysis
    asking_price = ad_data.get("asking_price", 0)

    market_price = tool.get(
        "market",
        {}
    ).get(
        "used_price_max"
    )

    if market_price is not None:

        if asking_price <= market_price:

            price_status = "acceptable"

            reasons.append(
                "Price is acceptable."
            )

            buy_score += 5

        else:

            price_status = "high"

            reasons.append(
                "Price is higher than market value."
            )

            buy_score -= 10

    else:

        price_status = "unknown"

        reasons.append(
            "Market price unavailable."
        )

    # Testing
    if has_test:

        reasons.append(
            "Seller allows testing."
        )

        buy_score += 5

    else:

        reasons.append(
            "No testing available."
        )

        risk_score += 10

    # Warranty
    if has_warranty:

        reasons.append(
            "Seller provides warranty."
        )

        buy_score += 5

    buy_score = max(
        0,
        min(100, round(buy_score))
    )

    risk_score = max(
        0,
        min(100, round(risk_score))
    )

    # Final decision
    if buy_score >= 85 and risk_score <= 40:

        decision = "BUY"

    elif buy_score >= 60 and risk_score <= 60:

        decision = "REVIEW"

    else:

        decision = "DON'T BUY"

    return {
        "decision": decision,
        "buy_score": buy_score,
        "risk_score": risk_score,
        "ad_score": ad_score,
        "has_test": has_test,
        "has_warranty": has_warranty,
        "price_status": price_status,
        "reasons": reasons
    }