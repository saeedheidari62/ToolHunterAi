from flask import Flask
from backend.backend.decision_engine import evaluate_tool

app = Flask(__name__)

@app.route("/")
def home():
    return "ToolHunterAI API is running"

@app.route("/search")
def search():
    sample_tool = {
        "price": 90,
        "tested": True
    }

    result = evaluate_tool(sample_tool)
    return result

if __name__ == "__main__":
    app.run()
