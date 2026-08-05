class RankEngine:
    """
    Compare multiple analyzed ads
    and select the best buying option
    """

    def __init__(self):
        pass


    def calculate_final_score(self, ad):

        score = ad.get("buy_score", 0)

        risk = ad.get("risk_score", 50)

        # Risk penalty
        score -= risk * 0.2


        reasons = ad.get("reasons", [])


        for reason in reasons:

            if "Testing" in reason or "testing" in reason:
                score += 3


            if "Warranty" in reason or "warranty" in reason:
                score += 5


        return round(score)



    def rank(self, results):

        if not results:
            return None


        for ad in results:

            ad["final_score"] = self.calculate_final_score(ad)


        ranked = sorted(
            results,
            key=lambda x: x.get("final_score", 0),
            reverse=True
        )


        best = ranked[0]


        return {
            "best_choice": best,

            "ranking": ranked,

            "total_ads": len(ranked)
        }