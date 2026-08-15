import json
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request

from collector import AdCollector
from diwar_collector import DiwarCollector
from decision_engine import make_decision
from ad_analyzer import analyze_ad
from tool_matcher import ToolMatcher
from rank_engine import RankEngine
from decision_explainer import DecisionExplainer
from history_manager import (
    save_history,
    get_history,
    get_history_by_id
)
from ad_normalizer import AdNormalizer

app = Flask(__name__)

collector = AdCollector()
diwar_collector = DiwarCollector()
matcher = ToolMatcher()
ranker = RankEngine()
explainer = DecisionExplainer()
normalizer = AdNormalizer()


def create_analysis_id():
    return str(uuid.uuid4())


def create_timestamp():
    return datetime.now(timezone.utc).isoformat()


def prepare_ad(ad):
    if not isinstance(ad, dict):
        return ad

    if "url" in ad:
        return diwar_collector.collect(ad)

    return ad


def analyze_single_ad(ad):
    ad = prepare_ad(ad)

    normalized = normalizer.normalize(ad)

    if not normalized["valid"]:
        return {
            "error": "Invalid advertisement data.",
            "errors": normalized["errors"]
        }

    ad = normalized["ad"]

    collected_ad = collector.collect(
        title=ad["title"],
        description=ad["description"],
        price=ad["price"],
        seller_type=ad["seller_type"],
        testing=ad.get("testing", False),
        warranty=ad.get("warranty", False),
        condition=ad.get("condition", "used")
    )

    tool_id = matcher.match(
        collected_ad["title"]
        + " "
        + collected_ad["description"]
        + " "
        + collected_ad.get("brand_model", "")
    )

    if not tool_id:
        return {
            "error": "Tool not recognized.",
            "title": collected_ad["title"]
        }

    ad_analysis = analyze_ad(collected_ad)

    decision_data = {
        "tool_name": tool_id,
        "asking_price": collected_ad["price"],
        "has_test": collected_ad["has_test"],
        "has_warranty": collected_ad["has_warranty"],
        "description": collected_ad["description"],
        "ad_score": ad_analysis["ad_score"],
        "analysis": ad_analysis["analysis"],
        "image_file": ad.get("image_file"),
    }

    result = make_decision(decision_data)

    result["has_test"] = collected_ad["has_test"]
    result["has_warranty"] = collected_ad["has_warranty"]

    result["price_status"] = result.get(
        "price_status"
    )

    result["price_difference_percent"] = result.get(
        "price_difference_percent"
    )

    result["ad_score"] = ad_analysis["ad_score"]
    result["tool"] = tool_id
    result["title"] = collected_ad["title"]

    return result


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Invalid or missing JSON data."
        }), 400

    if "ads" not in data:
        return jsonify({
            "error": "Field 'ads' is required."
        }), 400

    ads = data["ads"]

    if not isinstance(ads, list):
        return jsonify({
            "error": "Field 'ads' must be a list."
        }), 400

    if not ads:
        return jsonify({
            "error": "Ads list cannot be empty."
        }), 400

    results = []
    errors = []

    for index, ad in enumerate(ads):

        result = analyze_single_ad(ad)

        if "error" in result:
            errors.append({
                "index": index,
                "error": result
            })
        else:
            results.append(result)

    if not results:
        return jsonify({
            "error": "No valid ads could be analyzed.",
            "errors": errors
        }), 400

    final = ranker.rank(results)

    explanation = explainer.explain(
        final["best_choice"],
        final["ranking"]
    )

    analysis_id = create_analysis_id()
    created_at = create_timestamp()

    analysis_record = {
        "analysis_id": analysis_id,

        "created_at": created_at,
        "service": "ToolHunterAI API",
        "version": "2.0",
        "total_ads": final["total_ads"],
        "best_choice": final["best_choice"],
        "ranking": final["ranking"],
        "explanation": explanation,
        "errors": errors
    }

    save_history(analysis_record)

    return jsonify({
        "analysis_id": analysis_id,
        "created_at": created_at,
        "service": "ToolHunterAI API",
        "version": "2.0",
        "total_ads": final["total_ads"],
        "best_choice": final["best_choice"],
        "ranking": final["ranking"],
        "explanation": explanation,
        "errors": errors
    })


@app.route("/history", methods=["GET"])
def history():

    records = get_history()

    return jsonify({
        "service": "ToolHunterAI API",
        "total": len(records),
        "history": records
    })


@app.route("/history/<analysis_id>", methods=["GET"])
def history_detail(analysis_id):

    record = get_history_by_id(analysis_id)

    if record is None:
        return jsonify({
            "error": "Analysis not found.",
            "analysis_id": analysis_id
        }), 404

    return jsonify({
        "service": "ToolHunterAI API",
        "analysis": record
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
