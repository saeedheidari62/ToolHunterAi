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
    buy_score = tool["buy_score"]

    asking_price = ad_data.get("asking_price", 0)
    market_price = tool["market"].get("used_price_max")

    reasons = []

    if market_price is not None:
        if asking_price <= market_price:
            reasons.append("Price is acceptable.")
        else:
            reasons.append("Price is higher than market value.")
            buy_score -= 10

    if ad_data.get("has_test"):
        reasons.append("Seller allows testing.")
        buy_score += 5

    if ad_data.get("has_warranty"):
        reasons.append("Seller provides warranty.")
        buy_score += 5

    if risk_score <= 30 and buy_score >= 80:
        decision = "BUY"
    elif risk_score <= 60:
        decision = "REVIEW"
    else:
        decision = "DON'T BUY"

    return {
        "decision": decision,
        "buy_score": buy_score,
        "risk_score": risk_score,
        "reasons": reasons
    }