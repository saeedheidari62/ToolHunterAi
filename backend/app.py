from collector import AdCollector
from decision_engine import make_decision
from ad_analyzer import analyze_ad
from tool_matcher import ToolMatcher


collector = AdCollector()
matcher = ToolMatcher()


def main():

    print("=== ToolHunterAI ===")


    title = input("Ad Title: ")

    description = input(
        "Ad Description: "
    )

    price = int(
        input("Price: ")
    )

    seller_type = input(
        "Seller Type (Personal/Business): "
    )


    has_test = input(
        "Testing available? (y/n): "
    ).lower() == "y"


    has_warranty = input(
        "Warranty available? (y/n): "
    ).lower() == "y"


    condition = input(
        "Condition (New/Used): "
    )


    ad_data = collector.collect(
        title=title,
        description=description,
        price=price,
        seller_type=seller_type,
        testing=has_test,
        warranty=has_warranty,
        condition=condition
    )


    print("\nCollected Data:")
    print(ad_data)


    tool_id = matcher.match(
        title + " " + description
    )


    if not tool_id:

        print(
            "\nTool not recognized."
        )

        return


    print("\nDetected Tool:")
    print(tool_id)



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


    print("\n=== Decision ===")
    print(result)



if __name__ == "__main__":
    main()