import json
from pathlib import Path

from description_analyzer import analyze_description
from price_analyzer import analyze_price
from image_analyzer import analyze_image


def load_tool(tool_name):

    base_path = Path(__file__).resolve().parent.parent

    file_path = (
        base_path
        / "knowledge_base"
        / "tools"
        / f"{tool_name}.json"
    )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def make_decision(ad_data):

    tool_name = ad_data["tool_name"]
    tool = load_tool(tool_name)

    risk_score = tool["risk"]["score"]
    base_buy_score = tool["buy_score"]

    ad_score = ad_data.get("ad_score", 50)

    buy_score = (
        base_buy_score * 0.8
    ) + (
        ad_score * 0.2
    )

    reasons = []

    has_test = bool(
        ad_data.get("has_test")
    )

    has_warranty = bool(
        ad_data.get("has_warranty")
    )

    # Ad analysis reasons
    reasons.extend(
        ad_data.get("analysis", [])
    )

    # Description analysis
    description = ad_data.get(
        "description",
        ""
    )

    description_result = analyze_description(
        description
    )

    risk_score += description_result[
        "description_risk"
    ]

    reasons.extend(
        description_result[
            "description_reasons"
        ]
    )

    # Image analysis
    image_file = ad_data.get(
        "image_file"
    )

    image_result = analyze_image(
        image_file
    )

    risk_score += image_result[
        "image_risk"
    ]

    reasons.extend(
        image_result[
            "image_reasons"
        ]
    )

    # Price Engine v2
    asking_price = ad_data.get(
        "asking_price",
        0
    )

    price_result = analyze_price(
        tool,
        asking_price
    )

    price_status = price_result[
        "price_status"
    ]

    price_score = price_result[
        "price_score"
    ]

    price_difference_percent = price_result.get(
        "price_difference_percent"
    )

    reasons.extend(
        price_result["price_reason"]
    )

    # Price contribution to Buy Score
    price_adjustment = max(-10, min(7, (price_score - 50) * 0.15))

    buy_score += price_adjustment

    # Extra risk for suspiciously low prices
    if price_difference_percent is not None:

        if price_difference_percent <= -20:

            risk_score += 20

            reasons.append(
                "Price is significantly below market and requires verification."
            )

        elif price_difference_percent <= -10:

            risk_score += 10

            reasons.append(
                "Price is unusually low and requires verification."
            )

    # High price penalty
    if price_status == "HIGH_PRICE":

        risk_score += 5

    elif price_status == "VERY_HIGH_PRICE":

        risk_score += 15

    # Testing
    if has_test:

        reasons.append(
            "Seller allows testing."
        )

        buy_score += 3

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
        min(
            100,
            round(buy_score)
        )
    )

    risk_score = max(
        0,
        min(
            100,
            round(risk_score)
        )
    )

    # Final decision
    if (
        buy_score >= 85
        and risk_score <= 40
    ):

        decision = "BUY"

    elif (
        buy_score >= 60
        and risk_score <= 60
    ):

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
        "price_score": price_score,
        "price_difference_percent": (
            price_difference_percent
        ),
        "reasons": reasons
    }