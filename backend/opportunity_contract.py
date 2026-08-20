def build_opportunity_contract(result):
    """Convert an analyzed listing into a safe, explainable buyer opportunity."""
    result = dict(result or {})
    decision = str(result.get("decision", "REVIEW"))
    risk = float(result.get("risk_score", 100) or 100)
    score = float(result.get("opportunity_score", 0) or 0)

    if decision == "BUY" and risk <= 40 and score >= 60:
        status = "BUY_NOW"
    elif decision == "DON'T BUY" or risk > 75 or score < 40:
        status = "REJECT"
    else:
        status = "REVIEW"

    evidence = []
    price_diff = result.get("price_difference_percent")
    if isinstance(price_diff, (int, float)) and price_diff < 0:
        evidence.append(f"Price is {abs(price_diff):.1f}% below market.")
    elif isinstance(price_diff, (int, float)) and price_diff > 0:
        evidence.append(f"Price is {price_diff:.1f}% above market.")

    if result.get("tool") or result.get("matched_tools"):
        evidence.append("Tool identity matched.")
    if result.get("has_test"):
        evidence.append("Testing is available.")
    if result.get("has_warranty"):
        evidence.append("Warranty is available.")
    if risk <= 30:
        evidence.append("Risk level is low.")
    elif risk > 60:
        evidence.append("Risk level requires additional verification.")

    return {
        "status": status,
        "opportunity_score": score,
        "decision": decision,
        "risk_score": risk,
        "evidence": evidence,
        "tool": result.get("tool"),
        "title": result.get("title"),
        "price": result.get("asking_price", result.get("price", 0)),
        "url": result.get("url", ""),
        "city": result.get("city"),
    }
