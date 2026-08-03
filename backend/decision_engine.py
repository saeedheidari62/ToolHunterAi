import json
from pathlib import Path


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

    # Score from ad analyzer
    ad_score = ad_data.get("ad_score", 50)

    # Combine tool quality and ad quality
    buy_score = (base_buy_score * 0.8) + (ad_score * 0.2)

    asking_price = ad_data.get("asking_price", 0)
    market = tool.get("market", {})
    market_price = market.get("used_price_max")

    reasons = []

    # Price analysis
    if market_price is not None:
        if asking_price <= market_price:
            reasons.append("Price is acceptable.")
            buy_score += 5
        else:
            reasons.append("Price is higher than market value.")
            buy_score -= 10
    else:
        reasons.append("Market price unavailable.")

    # Test
    if ad_data.get("has_test"):
        reasons.append("Seller allows testing.")
        buy_score += 5
    else:
        reasons.append("No testing available.")
        risk_score += 10

    # Warranty
    if ad_data.get("has_warranty"):
        reasons.append("Seller provides warranty.")
        buy_score += 5

    # Keep values in range
    buy_score = max(0, min(100, round(buy_score)))
    risk_score = max(0, min(100, round(risk_score)))

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
        "reasons": reasons
    }