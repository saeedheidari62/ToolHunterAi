from decision_engine import make_decision

tool_name = "Bosch_GBH_2_26"

result = make_decision(tool_name)

print("Decision:", result["decision"])
print("Reason:", result["reason"])