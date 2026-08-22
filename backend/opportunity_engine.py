class OpportunityEngine:
    """Score and rank analyzed ads as market opportunities."""

    DECISION_BONUS = {"BUY": 20, "REVIEW": 8, "DON'T BUY": -20}

    def score(self, ad):
        buy = float(ad.get("buy_score", 0) or 0)
        risk = float(ad.get("risk_score", 50) or 50)
        ad_score = float(ad.get("ad_score", 0) or 0)
        price_diff = float(ad.get("price_difference_percent", 0) or 0)

        price_opportunity = max(-30.0, min(30.0, -price_diff * 0.30))
        quality = max(0.0, min(15.0, ad_score * 0.15))
        trust = 5.0 if ad.get("has_test") else 0.0
        trust += 5.0 if ad.get("has_warranty") else 0.0
        decision = self.DECISION_BONUS.get(ad.get("decision", "REVIEW"), 0)
        risk_component = max(-25.0, min(0.0, -(risk - 20.0) * 0.25))

        score = buy * 0.45 + price_opportunity + quality + trust + decision + risk_component
        return round(max(0.0, min(100.0, score)), 1)

    def rank(self, results, limit=None):
        ranked = []
        for ad in results or []:
            item = dict(ad)
            item["opportunity_score"] = self.score(item)
            if item.get("decision") == "DON'T BUY" or float(item.get("risk_score", 100) or 100) > 75:
                item["opportunity_status"] = "BLOCKED"
            elif item["opportunity_score"] >= 60:
                item["opportunity_status"] = "OPPORTUNITY"
            elif item["opportunity_score"] >= 40:
                item["opportunity_status"] = "WATCH"
            else:
                item["opportunity_status"] = "LOW_VALUE"
            ranked.append(item)

        ranked.sort(
            key=lambda x: (
                x.get("opportunity_status") != "BLOCKED",
                x["opportunity_score"],
                x.get("buy_score", 0),
                -x.get("risk_score", 100),
            ),
            reverse=True,
        )
        if limit is not None:
            ranked = ranked[:max(0, int(limit))]
        return {
            "total": len(ranked),
            "opportunities": ranked,
            "best_opportunity": next((item for item in ranked if item["opportunity_status"] != "BLOCKED"), None),
        }
