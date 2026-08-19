import json
from pathlib import Path

from .description_analyzer import analyze_description
from .price_analyzer import analyze_price
from .image_analyzer import analyze_image
from .image_downloader import ImageDownloader


def load_tool(tool_name):
    base_path = Path(__file__).resolve().parent.parent
    file_path = base_path / "knowledge_base" / "tools" / f"{tool_name}.json"
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def _normalize_market_confidence(value):
    if isinstance(value, str):
        normalized = value.strip().upper()
        if normalized in {"HIGH", "MEDIUM", "LOW", "NONE"}:
            return normalized
    if isinstance(value, (int, float)):
        if value >= 0.8:
            return "HIGH"
        if value >= 0.5:
            return "MEDIUM"
        if value > 0:
            return "LOW"
    return None


def make_decision(ad_data):
    image_downloader = ImageDownloader()
    tool_name = ad_data["tool_name"]
    tool = load_tool(tool_name)

    risk_score = tool["risk"]["score"]
    base_buy_score = tool["buy_score"]
    ad_score = ad_data.get("ad_score", 50)
    buy_score = (base_buy_score * 0.8) + (ad_score * 0.2)
    reasons = []

    has_test = bool(ad_data.get("has_test"))
    has_warranty = bool(ad_data.get("has_warranty"))
    reasons.extend(ad_data.get("analysis", []))

    description_result = analyze_description(ad_data.get("description", ""))
    risk_score += description_result["description_risk"]
    reasons.extend(description_result["description_reasons"])
    price_signal = description_result.get("price_signal", "NONE")

    image_urls = ad_data.get("image_urls", [])
    image_files = image_downloader.download(image_urls)
    if image_files:
        image_results = [analyze_image(image_file) for image_file in image_files]
        risk_score += max(result.get("image_risk", 0) for result in image_results)
        for result in image_results:
            reasons.extend(result.get("image_reasons", []))
    else:
        image_result = analyze_image(ad_data.get("image_file"))
        risk_score += image_result["image_risk"]
        reasons.extend(image_result["image_reasons"])

    asking_price = ad_data.get("asking_price", 0)
    market_data = ad_data.get("market_data")
    price_result = analyze_price(tool, asking_price, market_data=market_data)
    market_confidence = _normalize_market_confidence(price_result.get("market_confidence"))
    price_status = price_result["price_status"]
    price_score = price_result["price_score"]
    price_difference_percent = price_result.get("price_difference_percent")
    market_source = price_result.get("market_source", "knowledge_base")
    market_benchmark_reason = price_result.get("market_benchmark_reason", "")

    if price_signal != "PRICE_ON_REQUEST":
        reasons.extend(price_result["price_reason"])

    if price_signal == "PRICE_ON_REQUEST":
        price_status = "SUSPICIOUS_PRICE"
        price_score = 50
        risk_score += 25
        reasons.extend([
            "The listed price may be symbolic or not the actual selling price.",
            "The seller asks the buyer to contact them for the current price.",
        ])

    buy_score += max(-10, min(7, (price_score - 50) * 0.15))

    if price_signal != "PRICE_ON_REQUEST" and price_difference_percent is not None:
        if price_difference_percent <= -20:
            risk_score += 20
        elif price_difference_percent <= -10:
            risk_score += 10

    if price_status == "HIGH_PRICE":
        risk_score += 5
    elif price_status == "VERY_HIGH_PRICE":
        risk_score += 15

    if has_test:
        reasons.append("Seller allows testing.")
        buy_score += 3
    else:
        reasons.append("No testing available.")
        risk_score += 10

    if has_warranty:
        reasons.append("Seller provides warranty.")
        buy_score += 5

    buy_score = max(0, min(100, round(buy_score)))
    risk_score = max(0, min(100, round(risk_score)))

    dynamic_market = market_source in {"dynamic", "dynamic_divar"}
    if price_signal == "PRICE_ON_REQUEST":
        decision = "REVIEW"
    elif not has_test and not has_warranty:
        decision = "REVIEW"
    elif market_confidence == "LOW" and dynamic_market:
        decision = "REVIEW"
    elif buy_score >= 85 and risk_score <= 40:
        decision = "BUY"
    elif buy_score >= 60 and risk_score <= 70:
        decision = "REVIEW"
    else:
        decision = "DON'T BUY"

    if decision == "BUY":
        decision_reason = "The price, advertisement quality, and risk profile meet the BUY threshold."
        next_action = "Perform final physical verification before payment."
    elif decision == "DON'T BUY":
        decision_reason = "The combined price, advertisement, or risk signals do not meet the purchase threshold."
        next_action = "Reject this listing and compare another seller."
    elif market_confidence == "LOW" and dynamic_market:
        decision_reason = "Dynamic market confidence is LOW, so the live price benchmark is not strong enough for a final purchase decision."
        next_action = "Collect at least 2 comparable listings before making a final decision."
    elif not has_test and not has_warranty:
        decision_reason = "Seller verification is insufficient because neither testing nor warranty is available."
        next_action = "Request an in-person test and confirm warranty or return terms before payment."
    elif price_status in ("HIGH_PRICE", "VERY_HIGH_PRICE"):
        decision_reason = "The asking price is above the selected market benchmark."
        next_action = "Negotiate toward the market range or compare another listing."
    else:
        decision_reason = "The current signals are not strong enough for an immediate BUY."
        next_action = "Verify the tool physically and re-check the market price before payment."

    return {
        "decision": decision,
        "decision_reason": decision_reason,
        "next_action": next_action,
        "asking_price": asking_price,
        "buy_score": buy_score,
        "risk_score": risk_score,
        "ad_score": ad_score,
        "has_test": has_test,
        "has_warranty": has_warranty,
        "market_confidence": market_confidence,
        "market_source": market_source,
        "market_benchmark_reason": market_benchmark_reason,
        "price_status": price_status,
        "price_score": price_score,
        "price_difference_percent": price_difference_percent,
        "reasons": reasons,
    }
