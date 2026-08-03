from ad_analyzer import analyze_ad
from decision_engine import make_decision


def main():
    tool_name = input(
        "Enter tool id (example: bosch_gbh_2_26 or makita_hr2470): "
    ).strip()

    sample_ad = {
        "tool_name": tool_name,
        "asking_price": 8500000,
        "seller_type": "Personal",
        "has_test": True,
        "has_warranty": False,
        "condition": "Used"
    }

    # Analyze advertisement
    analyzed_ad = analyze_ad(sample_ad)

    # Make final decision
    result = make_decision(analyzed_ad)

    print("\n========== ToolHunterAI ==========")
    print(f"Tool: {analyzed_ad['tool_name']}")
    print(f"Price: {analyzed_ad['asking_price']}")
    print(f"Decision: {result['decision']}")
    print(f"Buy Score: {result['buy_score']}")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Ad Score: {result.get('ad_score', 'N/A')}")

    print("\nReasons:")
    for reason in result["reasons"]:
        print(f"- {reason}")


if __name__ == "__main__":
    main()