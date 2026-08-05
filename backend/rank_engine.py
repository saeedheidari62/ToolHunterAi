class RankEngine:
    """
    Compare multiple analyzed ads
    and select the best buying option
    """


    def __init__(self):
        pass


    def rank(self, results):

        if not results:
            return None


        ranked = sorted(
            results,
            key=lambda x: (
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