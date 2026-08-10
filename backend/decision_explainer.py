class DecisionExplainer:

    def explain(self, result, ranking=None):

        if not result:
            return None

        decision = result.get("decision", "REVIEW")
        buy_score = result.get("buy_score", 0)
        risk_score = result.get("risk_score", 0)
        final_score = result.get("final_score", buy_score)

        strengths = []
        risks = []
        warnings = []
        checks = []

        if result.get("has_test"):
            strengths.append("Testing is available.")
        else:
            risks.append("Testing is not available.")
            warnings.append("Tool must be tested before purchase.")
            checks.append("Test the tool under real operating conditions.")

        if result.get("has_warranty"):
            strengths.append("Warranty is available.")
        else:
            risks.append("No warranty is provided.")
            warnings.append("There is no warranty protection.")
            checks.append("Inspect the tool carefully because there is no warranty.")

        price_status = result.get("price_status", "unknown")

        if price_status == "acceptable":
            strengths.append("Price is acceptable compared with the market.")
        elif price_status == "high":
            risks.append("Price is higher than the expected market value.")
            warnings.append("Asking price is above market value.")
            checks.append("Compare the price with similar listings.")
        else:
            risks.append("Market price could not be verified.")
            checks.append("Compare the price with similar listings.")

        if risk_score <= 30:
            strengths.append("Risk level is low.")
        elif risk_score <= 60:
            risks.append("Risk level is moderate.")
        else:
            risks.append("Risk level is high.")
            warnings.append("Overall risk is high.")
            checks.append("Perform a detailed inspection before purchase.")

        if decision == "BUY":
            summary = "This listing is currently a strong buying option."
            detail = "Buying can be considered after completing the recommended checks."
        elif decision == "REVIEW":
            summary = "This listing requires further review before buying."
            detail = "Do not purchase until the identified risks are checked."
        else:
            summary = "This listing is currently not recommended for purchase."
            detail = "Avoid purchasing unless the negative factors are resolved."

        comparison = []

        if ranking:
            for index, item in enumerate(ranking, start=1):
                comparison.append({
                    "rank": index,
                    "tool": item.get("tool"),
                    "title": item.get("title"),
                    "final_score": item.get("final_score", 0),
                    "buy_score": item.get("buy_score", 0),
                    "risk_score": item.get("risk_score", 0)
                })

        ranking_reason = "Ranking comparison is not available."

        if len(comparison) >= 2:
            first = comparison[0]
            second = comparison[1]

            difference = (
                first["final_score"] - second["final_score"]
            )

            if difference > 0:
                ranking_reason = (
                    f"This listing ranked first with a "
                    f"{difference}-point final-score advantage."
                )
            elif difference == 0:
                ranking_reason = (
                    "This listing tied on final score and was "
                    "selected using ranking tie-breakers."
                )

        return {
            "summary": summary,
            "recommendation": decision,
            "recommendation_detail": detail,
            "scores": {
                "buy_score": buy_score,
                "risk_score": risk_score,
                "final_score": final_score
            },
            "strengths": strengths,
            "risks": risks,
            "warnings": warnings,
            "ranking_reason": ranking_reason,
            "comparison": comparison,
            "checks_before_purchase": checks
        }
