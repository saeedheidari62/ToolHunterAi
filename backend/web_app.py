from flask import Flask, jsonify, redirect, render_template, request, url_for

from backend.alert_engine import AlertEngine
from backend.api import analyze_single_ad
from backend.auto_scanner import AutoScanner
from backend.deal_events import DealEventLedger
from backend.discovery_service import DiscoveryService
from backend.monitoring_controller import MonitoringController
from backend.tool_catalog import ToolCatalog
from backend.watchlist_store import WatchlistStore
from backend.history_manager import get_history

app = Flask(__name__)
auto_scanner = AutoScanner()
discovery_service = DiscoveryService()
tool_catalog = ToolCatalog()
alert_engine = AlertEngine(DealEventLedger())
monitoring = MonitoringController(auto_scanner, WatchlistStore())


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "ToolHunterAI Web", "ai_discovery_enabled": True, "api_version": "v1", "catalog_size": len(tool_catalog.all()), "monitoring": monitoring.status()}), 200


@app.route("/catalog", methods=["GET"])
def catalog():
    return jsonify({"tools": tool_catalog.all()}), 200


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    if request.method == "GET": return render_template("analysis.html")
    data = request.get_json(silent=True) or request.form
    url = data.get("url", "")
    if not url: return jsonify({"error": "INVALID_INPUT", "message": "url is required."}), 400
    try: result = analyze_single_ad(url)
    except Exception as exc: return jsonify({"error": "ANALYSIS_FAILED", "message": str(exc)}), 500
    if isinstance(result, dict) and result.get("error"): return jsonify(result), 400
    return render_template("result.html", result=result)


@app.route("/discover", methods=["POST"])
def discover():
    data = request.get_json(silent=True) or request.form
    city, query, variant = data.get("city"), data.get("query"), data.get("variant")
    result = discovery_service.discover(city, query, variant=variant, limit=data.get("limit", 10))
    if result.get("error"): return jsonify(result), 400
    return jsonify(result)


def _positive_int(value, default, maximum):
    try: parsed = int(value)
    except (TypeError, ValueError): return default
    return min(max(parsed, 1), maximum)


@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json(silent=True) or request.form
    cities = data.get("cities", data.get("city", []))
    tool_ids = data.get("tool_ids", data.get("tool_id", []))
    if isinstance(cities, str): cities = [x.strip() for x in cities.split(",") if x.strip()]
    if isinstance(tool_ids, str): tool_ids = [x.strip() for x in tool_ids.split(",") if x.strip()]
    cities = list(dict.fromkeys(cities))[:6]
    if not cities: return jsonify({"error": "INVALID_SCAN_INPUT", "message": "at least one city is required."}), 400
    if tool_ids:
        unknown = [x for x in tool_ids if x not in set(tool_catalog.ids())]
        if unknown: return jsonify({"error": "INVALID_SCAN_INPUT", "message": "unknown tool id(s)", "unknown_tool_ids": unknown}), 400
    result = auto_scanner.scan_cities(cities, limit_per_tool=_positive_int(data.get("limit_per_tool", 5), 5, 5), top_n=_positive_int(data.get("top_n", 10), 10, 50), tool_ids=tool_ids or None)
    if result.get("error"): return jsonify(result), 400
    return jsonify(result)


@app.route("/alerts", methods=["GET"])
def alerts():
    return jsonify({"alerts": alert_engine.recent(limit=_positive_int(request.args.get("limit", 10), 10, 50), min_priority=_positive_int(request.args.get("min_priority", 70), 70, 100))}), 200


@app.route("/monitoring/watch", methods=["POST"])
def monitoring_watch():
    data = request.get_json(silent=True) or request.form
    watch_id = str(data.get("watch_id", "")).strip()
    cities = data.get("cities", [])
    tool_ids = data.get("tool_ids")
    if isinstance(cities, str): cities = [x.strip() for x in cities.split(",") if x.strip()]
    if isinstance(tool_ids, str): tool_ids = [x.strip() for x in tool_ids.split(",") if x.strip()]
    if not watch_id or not cities: return jsonify({"error": "INVALID_MONITORING_INPUT", "message": "watch_id and cities are required."}), 400
    watch = monitoring.upsert_watch(watch_id, cities, _positive_int(data.get("interval_seconds", 3600), 3600, 86400), tool_ids, _positive_int(data.get("top_n", 10), 10, 50), bool(data.get("enabled", True)))
    return jsonify({"watch": watch}), 200


@app.route("/monitoring/status", methods=["GET"])
def monitoring_status():
    return jsonify(monitoring.status()), 200


@app.route("/monitoring/run/<watch_id>", methods=["POST"])
def monitoring_run(watch_id):
    result = monitoring.run_now(watch_id)
    return jsonify(result), 200 if result.get("status") != "NOT_FOUND" else 404


@app.route("/history")
def history():
    return render_template("history.html", history=get_history())


@app.route("/dashboard")
def dashboard():
    data = get_history()
    return render_template("dashboard.html", data=data, total=len(data), buys=sum(1 for x in data if x.get("decision") == "BUY"), reviews=sum(1 for x in data if x.get("decision") == "REVIEW"))