from flask import Flask, jsonify, render_template, request

from backend.api import ai_tool_discovery, analyze_single_ad, explainer
from backend.discovery_service import DiscoveryService
from backend.auto_scanner import AutoScanner
from backend.history_manager import get_history, save_history


app = Flask(__name__)
discovery_service = DiscoveryService()
auto_scanner = AutoScanner(discovery_service=discovery_service)


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
        return render_template("result.html", result={
            "error": "INVALID_AD", "error_code": "INVALID_AD", "message": "لینک آگهی دیوار وارد نشده است.",
        }), 400
    result = analyze_single_ad({"url": url})
    if "error" in result:
        return render_template("result.html", result=result), 400
    result["explanation"] = explainer.explain(result)
    save_history({
        "tool_name": result.get("tool", ""), "price": result.get("asking_price", 0),
        "decision": result.get("decision", ""), "buy_score": result.get("buy_score", 0),
        "risk_score": result.get("risk_score", 0), "ad_score": result.get("ad_score", 0),
        "market_source": result.get("market_source"),
    })
    return render_template("result.html", result=result)


@app.route("/discover", methods=["POST"])
def discover():
    data = request.get_json(silent=True) or request.form
    city = str(data.get("city", "")).strip()
    query = str(data.get("query", "")).strip()
    variant = data.get("variant")
    limit = data.get("limit", 5)
    result = discovery_service.discover(city, query, variant=variant, limit=limit)
    if result.get("error"):
        return jsonify(result), 400
    return jsonify(result)


@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json(silent=True) or request.form
    if hasattr(data, "getlist"):
        cities = data.getlist("cities") or data.getlist("city")
        tool_ids = data.getlist("tool_ids") or data.getlist("tool_id")
    else:
        cities = data.get("cities", data.get("city", []))
        tool_ids = data.get("tool_ids", data.get("tool_id", []))
    if isinstance(cities, str):
        cities = [item.strip() for item in cities.split(",") if item.strip()]
    if isinstance(tool_ids, str):
        tool_ids = [item.strip() for item in tool_ids.split(",") if item.strip()]
    if not cities:
        return jsonify({"error": "INVALID_SCAN_INPUT", "message": "at least one city is required."}), 400
    result = auto_scanner.scan_cities(
        cities,
        limit_per_tool=data.get("limit_per_tool", 5),
        top_n=data.get("top_n"),
        tool_ids=tool_ids or None,
    )
    if result.get("error"):
        return jsonify(result), 400
    return jsonify(result)


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
    return render_template("dashboard.html", total=total, buy=buy, review=review, dont_buy=dont_buy, avg_buy=avg_buy)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
