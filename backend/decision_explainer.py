class DecisionExplainer:
    """
    Convert decision and ranking data
    into a structured, user-friendly explanation.
    """

    def __init__(self):
        pass

    def explain(self, result, ranking=None):

        if not result:
            return None

        strengths = []
        risks = []

        # Recommendation
        decision = result.get("decision", "REVIEW")

        # Score information
        buy_score = result.get("buy_score", 0)
        risk_score = result.get("risk_score", 0)
        final_score = result.get(
            "final_score",
            buy_score
        )

        # Testing
        if result.get("has_test"):
            strengths.append(
                "Testing is available."
            )
        else:
            risks.append(
                "Testing is not available."
            )

        # Warranty
        if result.get("has_warranty"):
            strengths.append(
                "Warranty is available."
            )
        else:
            risks.append(
                "No warranty is provided."
            )

        # Price
        price_status = result.get(
            "price_status",
            "unknown"
        )

        if price_status == "acceptable":
            strengths.append(
                "Price is acceptable compared with the market."
            )

        elif price_status == "high":
            risks.append(
                "Price is higher than the expected market value."
            )

        else:
            risks.append(
                "Market price could not be verified."
            )

        # Risk level
        if risk_score <= 30:
            strengths.append(
                "Risk level is low."
            )

        elif risk_score <= 60:
            risks.append(
                "Risk level is moderate."
            )

        else:
            risks.append(
                "Risk level is high."
            )

        # Summary
        if decision == "BUY":
            summary = (
                "This listing is currently a strong buying option."
            )

        elif decision == "REVIEW":
            summary = (
                "This listing requires further review before buying."
            )

        else:
            summary = (
                "This listing is not recommended for purchase."
            )

        # Comparison
        comparison = []

        if ranking:

            for index, item in enumerate(ranking, start=1):

                comparison.append({
                    "rank": index,
                    "tool": item.get("tool"),
                    "title": item.get("title"),
                    "final_score": item.get(
                        "final_score",
                        0
                    ),
                    "buy_score": item.get(
                        "buy_score",
                        0
                    ),
                    "risk_score": item.get(
                        "risk_score",
                        0
                    )
                })

        return {
            "summary": summary,
            "recommendation": decision,
            "buy_score": buy_score,
            "risk_score": risk_score,
            "final_score": final_score,
            "strengths": strengths,
            "risks": risks,
            "comparison": comparison
        }