from flask import Flask, jsonify, redirect, render_template, request, url_for

from backend.api import analyze_single_ad
from backend.auto_scanner import AutoScanner
from backend.discovery_service import DiscoveryService

app = Flask(__name__)
auto_scanner = AutoScanner()
discovery_service = DiscoveryService()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    if request.method == "GET":
        return render_template("analysis.html")

    data = request.get_json(silent=True) or request.form
    url = data.get("url", "")
    if not url:
        return jsonify({"error": "INVALID_INPUT", "message": "url is required."}), 400

    try:
        result = analyze_single_ad(url)
    except Exception as exc:
        return jsonify({"error": "ANALYSIS_FAILED", "message": str(exc)}), 500

    if isinstance(result, dict) and result.get("error"):
        return jsonify(result), 400
    return render_template("result.html", result=result)


@app.route("/discover", methods=["POST"])
def discover():
    data = request.get_json(silent=True) or request.form
    city = data.get("city")
    query = data.get("query")
    variant = data.get("variant")
    limit = data.get("limit", 10)
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

    limit_per_tool = data.get("limit_per_tool", 5)
    top_n = data.get("top_n")

    # Keep compatibility with the original single-city scanner contract while
    # using the multi-city scanner whenever the production object supports it.
    if hasattr(auto_scanner, "scan_cities"):
        result = auto_scanner.scan_cities(
            cities,
            limit_per_tool=limit_per_tool,
            top_n=top_n,
            tool_ids=tool_ids or None,
        )
    else:
        result = auto_scanner.scan(cities[0], limit_per_tool)

    if result.get("error"):
        return jsonify(result), 400
    return jsonify(result)


@app.route("/history")
def history():
    return render_template("history.html", history=[])


@app.route("/dashboard")
def dashboard():
    data = []
    total = len(data)
    return render_template("dashboard.html", data=data, total=total)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
