from flask import Flask, jsonify, redirect, render_template, request, url_for

from backend.api import analyze_single_ad
from backend.auto_scanner import AutoScanner
from backend.discovery_service import DiscoveryService
from backend.tool_catalog import ToolCatalog

app = Flask(__name__)
auto_scanner = AutoScanner()
discovery_service = DiscoveryService()
tool_catalog = ToolCatalog()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "ToolHunterAI Web",
        "ai_discovery_enabled": True,
    }), 200


@app.route("/catalog", methods=["GET"])
def catalog():
    return jsonify({"tools": tool_catalog.all()}), 200


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


def _positive_int(value, default, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return min(max(parsed, 1), maximum)


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
    cities = list(dict.fromkeys(cities))[:6]
    if not cities:
        return jsonify({"error": "INVALID_SCAN_INPUT", "message": "at least one city is required."}), 400
    if tool_ids:
        known_ids = set(tool_catalog.ids())
        unknown = [tool_id for tool_id in tool_ids if tool_id not in known_ids]
        if unknown:
            return jsonify({
                "error": "INVALID_SCAN_INPUT",
                "message": "unknown tool id(s)",
                "unknown_tool_ids": unknown,
            }), 400
    limit_per_tool = _positive_int(data.get("limit_per_tool", 5), 5, 5)
    top_n = _positive_int(data.get("top_n", 10), 10, 50)
    scan_cities = getattr(auto_scanner, "scan_cities", None)
    if scan_cities is not None:
        result = scan_cities(
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
    return render_template("history.html", history=get_history())


@app.route("/dashboard")
def dashboard():
    data = get_history()
    total = len(data)
    buys = sum(1 for item in data if item.get("decision") == "BUY")
    reviews = sum(1 for item in data if item.get("decision") == "REVIEW")
    return render_template("dashboard.html", data=data, total=total, buys=buys, reviews=reviews)
