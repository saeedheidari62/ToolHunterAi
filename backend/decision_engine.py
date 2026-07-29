import json
from pathlib import Path


def load_tool(tool_name):
    base_path = Path(__file__).resolve().parent.parent
    file_path = base_path / "knowledge_base" / "tools" / f"{tool_name}.json"

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def make_decision(tool_name):
    tool = load_tool(tool_name)

    risk_score = tool["risk"]["score"]
    buy_score = tool["buy_score"]

    if risk_score <= 30 and buy_score >= 80:
        return {
            "decision": "BUY",
            "reason": "Low risk and high buy score."
        }

    elif risk_score <= 60:
        return {
            "decision": "REVIEW",
            "reason": "Needs more inspection before purchase."
        }

    else:
        return {
            "decision": "DON'T BUY",
            "reason": "Risk is too high."
        }