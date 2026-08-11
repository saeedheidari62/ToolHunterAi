class RankEngine:
    """
    Compare multiple analyzed ads
    and select the best buying option.
    """

    def __init__(self):
        pass

    def calculate_final_score(self, ad):

        score = ad.get("buy_score", 0)

        risk = ad.get("risk_score", 50)

        # Risk penalty
        score -= risk * 0.2

        # Testing bonus
        if ad.get("has_test", False):
            score += 3

        # Warranty bonus
        if ad.get("has_warranty", False):
            score += 5

        # Keep score within a clear 0-100 range
        score = max(0, min(100, score))

        return round(score)

    def rank(self, results):

        if not results:
            return None

        for ad in results:
            ad["final_score"] = self.calculate_final_score(ad)

        decision_priority = {
            "BUY": 3,
            "REVIEW": 2,
            "DON'T BUY": 1
        }

        ranked = sorted(
            results,
            key=lambda x: (
                decision_priority.get(
                    x.get("decision", "REVIEW"),
                    1
                ),
                x.get("final_score", 0),
                x.get("buy_score", 0),
                -x.get("risk_score", 100)
            ),
            reverse=True
        )

        best = ranked[0]

        return {
            "best_choice": best,
            "ranking": ranked,
            "total_ads": len(ranked)
        }
