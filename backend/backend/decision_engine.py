def evaluate_tool(tool_data):
    price = tool_data.get("price", 0)
    tested = tool_data.get("tested", False)

    if tested and price <= 100:
        return {
            "decision": "BUY",
            "reason": "Price is good and tool was tested."
        }

    if tested:
        return {
            "decision": "REVIEW",
            "reason": "Tool passed the test but price is high."
        }

    return {
        "decision": "AVOID",
        "reason": "Tool was not tested."
    }
