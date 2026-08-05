from collector import AdCollector
from decision_engine import make_decision
from ad_analyzer import analyze_ad
from tool_matcher import ToolMatcher
from rank_engine import RankEngine


collector = AdCollector()
matcher = ToolMatcher()
ranker = RankEngine()


def analyze_single_ad(ad_data):

    tool_id = matcher.match(
        ad_data["title"] + " " + ad_data["description"]
    )


    if not tool_id:
        return None


    ad_analysis = analyze_ad(
        ad_data
    )


    decision_data = {

        "tool_name": tool_id,

        "asking_price": ad_data["price"],

        "has_test": ad_data["has_test"],

        "has_warranty": ad_data["has_warranty"],

        "description": ad_data["description"],

        "ad_score": ad_analysis["ad_score"],

        "analysis": ad_analysis["analysis"]

    }


    result = make_decision(
        decision_data
    )


    result["tool"] = tool_id
    result["title"] = ad_data["title"]

    return result



def main():

    print("=== ToolHunterAI Multi Ad ===")


    ads = [

        {
            "title": "Bosch GBH226",
            "description": "Used Bosch original with testing",
            "price": 8500000,
            "seller_type": "personal",
            "testing": True,
            "warranty": False,
            "condition": "used"
        },

        {
            "title": "ماکیتا 2470",
            "description": "Makita original used with testing",
            "price": 7000000,
            "seller_type": "business",
            "testing": True,
            "warranty": True,
            "condition": "used"
        }

    ]


    collected_ads = collector.collect_many(
        ads
    )


    results = []


    for ad in collected_ads:

        print("\nAnalyzing:")
        print(ad["title"])


        result = analyze_single_ad(ad)


        if result:
            print(result)
            results.append(result)



    final = ranker.rank(
        results
    )


    print("\n=== BEST DEAL ===")
    print(final)



if __name__ == "__main__":
    main()