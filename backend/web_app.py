from flask import Flask, jsonify, render_template, request

from backend.api import ai_tool_discovery, analyze_single_ad
from backend.history_manager import get_history, save_history


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "service": "ToolHunterAI Web",
        "status": "ok",
        "ai_discovery_enabled": ai_tool_discovery.enabled(),
    })


@app.route("/analyze", methods=["POST"])
def analyze():
    url = request.form.get("url", "").strip()
    if not url:
        return render_template(
            "result.html",
            result={
                "error": "INVALID_AD",
                "message": "لینک آگهی دیوار وارد نشده است.",
            },
        ), 400

    # Keep the web UI on the exact same production pipeline as the API:
    # URL -> fetch/normalize -> tool detection -> AI discovery/validation/
    # promotion -> market/risk/decision -> explanation.
    result = analyze_single_ad({"url": url})

    if "error" in result:
        return render_template("result.html", result=result), 400

    save_history({
        "tool_name": result.get("tool", ""),
        "price": result.get("asking_price", 0),
        "decision": result.get("decision", ""),
        "buy_score": result.get("buy_score", 0),
        "risk_score": result.get("risk_score", 0),
        "ad_score": result.get("ad_score", 0),
        "market_source": result.get("market_source"),
        "analysis_id": result.get("analysis_id"),
    })

    return render_template("result.html", result=result)


@app.route("/history")
def history():
    return render_template("history.html", history=get_history())


@app.route("/dashboard")
def dashboard():
    data = get_history()
    total = len(data)
    buy = sum(1 for x in data if x.get("decision") == "BUY")
    review = sum(1 for x in data if x.get("decision") == "REVIEW")
    dont_buy = sum(1 for x in data if x.get("decision") == "DON'T BUY")
    avg_buy = round(sum(x.get("buy_score", 0) for x in data) / total, 1) if total else 0

    return render_template(
        "dashboard.html",
        total=total,
        buy=buy,
        review=review,
        dont_buy=dont_buy,
        avg_buy=avg_buy,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
