from ad_analyzer import analyze_ad
from decision_engine import make_decision

sample_ad = {
    "tool_name": "Bosch_GBH_2_26",
    "asking_price": 8500000,
    "seller_type": "Personal",
    "has_test": True,
    "has_warranty": False,
    "condition": "Used"
}

analyzed = analyze_ad(sample_ad)

result = make_decision(analyzed["tool_name"])

print("===== ToolHunterAI =====")
print("Tool:", analyzed["tool_name"])
print("Price:", analyzed["asking_price"])
print("Decision:", result["decision"])
print("Reason:", result["reason"])