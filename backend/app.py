from ad_analyzer import analyze_ad
from decision_engine import make_decision


def yes_no_input(message):
    answer = input(message).strip().lower()
    return answer in ["y", "yes"]


def main():
    print("========== ToolHunterAI ==========\n")

    tool_name = input("Tool ID: ").strip()
    asking_price = int(input("Asking Price: "))
    seller_type = input("Seller Type (Personal/Business): ").strip().title()
    has_test = yes_no_input("Testing available? (y/n): ")
    has_warranty = yes_no_input("Warranty available? (y/n): ")
    condition = input("Condition (New/Used): ").strip().title()
    description = input("Description: ").strip()

    ad_data = {
        "tool_name": tool_name,
        "asking_price": asking_price,
        "seller_type": seller_type,
        "has_test": has_test,
        "has_warranty": has_warranty,
        "condition": condition,
        "description": description
    }

    analyzed_ad = analyze_ad(ad_data)
    result = make_decision(analyzed_ad)

    print("\n========== RESULT ==========")
    print(f"Tool: {tool_name}")
    print(f"Price: {asking_price:,}")
    print(f"Decision: {result['decision']}")
    print(f"Buy Score: {result['buy_score']}")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Ad Score: {result['ad_score']}")

    print("\nReasons:")
    for reason in result["reasons"]:
        print(f"- {reason}")


if __name__ == "__main__":
    main()