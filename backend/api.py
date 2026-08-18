import json
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request

from .collector import AdCollector
from .diwar_collector import DiwarCollector
from .diwar_fetcher import DiwarFetcher
from .decision_engine import make_decision
from .ad_analyzer import analyze_ad
from .tool_matcher import ToolMatcher
from .multi_tool_analyzer import MultiToolAnalyzer
from .rank_engine import RankEngine
from .decision_explainer import DecisionExplainer
from .history_manager import (
    save_history,
    get_history,
    get_history_by_id
)
from .ad_normalizer import AdNormalizer
from .divar_search_engine import DivarSearchEngine

app = Flask(__name__)

collector = AdCollector()
diwar_collector = DiwarCollector()
diwar_fetcher = DiwarFetcher()
matcher = ToolMatcher()
multi_tool_analyzer = MultiToolAnalyzer()
ranker = RankEngine()
explainer = DecisionExplainer()
normalizer = AdNormalizer()
divar_search_engine = DivarSearchEngine()


def create_analysis_id():
    return str(uuid.uuid4())


def create_timestamp():
    return datetime.now(timezone.utc).isoformat()


def prepare_ad(ad):
    if not isinstance(ad, dict):
        return ad

    if "url" not in ad:
        return ad

    url = str(ad.get("url", "")).strip()

    if not url:
        return ad

    fetched_ad = diwar_fetcher.fetch(url)

    if not isinstance(fetched_ad, dict):
        return {
            "_prepare_error": "Divar advertisement could not be fetched."
        }

    collected_ad = diwar_collector.collect(fetched_ad)

    if not isinstance(collected_ad, dict):
        return {
            "_prepare_error": "Divar advertisement could not be collected."
        }

    return collected_ad


def get_dynamic_market_data(
    tool_name,
    city="tehran"
):
    """
    Search Divar for the tool and calculate
    a dynamic market price snapshot.

    If dynamic search fails or produces insufficient
    data, return None so the static Knowledge Base
    remains the fallback.
    """

    city_map = {
        "تهران": "tehran",
        "teران": "tehran",
        "tehran": "tehran",
        "کرج": "karaj",
        "karaj": "karaj",
        "مشهد": "mashhad",
        "mashhad": "mashhad",
        "اصفهان": "isfahan",
        "isfahan": "isfahan",
        "شیراز": "shiraz",
        "shiraz": "shiraz",
        "تبریز": "tabriz",
        "tabriz": "tabriz",
    }

    city_slug = city_map.get(
        str(city or "").strip().lower(),
        "tehran"
    )

    try:
        search_result = divar_search_engine.search(
            city_slug,
            tool_name
        )

        filtered = divar_search_engine.filter_results(
            search_result.get("results", []),
            tool_name
        )

        if len(filtered) < 2:
            return None

        market_data = (
            divar_search_engine.get_market_prices({
                "results": filtered
            })
        )

        if not market_data.get("valid"):
            return None

        if market_data.get("sample_count", 0) < 2:
            return None

        return market_data

    except Exception:
        return None


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

    match_text = (
        collected_ad["title"]
        + " "
        + collected_ad["description"]
        + " "
        + collected_ad.get("brand_model", "")
    )

    tool_ids = matcher.match_all(match_text)

    if not tool_ids:
        return {
            "error": "Tool not recognized.",
            "title": collected_ad["title"],
            "matched_tools": []
        }

    if len(tool_ids) > 1:
        multi_result = multi_tool_analyzer.analyze(
            collected_ad["description"],
            tool_ids
        )

        ad_analysis = analyze_ad(collected_ad)

        individual_results = []

        for item in multi_result["tools"]:

            tool_id = item["tool_id"]
            asking_price = item["asking_price"]

            decision_data = {
                "tool_name": tool_id,
                "asking_price": asking_price or 0,
                "has_test": collected_ad["has_test"],
                "has_warranty": collected_ad["has_warranty"],
                "description": item["text"],
                "ad_score": ad_analysis["ad_score"],
                "analysis": ad_analysis["analysis"],
                "image_file": ad.get("image_file"),
                "image_urls": ad.get("image_urls", []),
            }

            decision = make_decision(decision_data)

            individual_results.append({
                "tool_id": tool_id,
                "asking_price": asking_price,
                "decision": decision
            })

        return {
            "error": "Multiple tools detected.",
            "title": collected_ad["title"],
            "matched_tools": tool_ids,
            "multi_tool_analysis": multi_result,
            "individual_results": individual_results,
            "decision": "REVIEW",
            "reason": (
                "Multiple tools were detected and each tool "
                "was analyzed independently."
            )
        }

    tool_id = tool_ids[0]

    ad_analysis = analyze_ad(collected_ad)

    market_data = get_dynamic_market_data(
        tool_id,
        collected_ad.get("city", "tehran")
    )

    decision_data = {
        "tool_name": tool_id,
        "asking_price": collected_ad["price"],
        "market_data": market_data,
        "has_test": collected_ad["has_test"],
        "has_warranty": collected_ad["has_warranty"],
        "description": collected_ad["description"],
        "ad_score": ad_analysis["ad_score"],
        "analysis": ad_analysis["analysis"],
        "image_file": ad.get("image_file"),
        "image_urls": ad.get("image_urls", []),
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
    result["market_data"] = market_data

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

        if isinstance(ad, dict) and "url" in ad:
            prepared_ad = prepare_ad(ad)

            if not isinstance(prepared_ad, dict):
                result = {
                    "error": "Invalid advertisement data.",
                    "errors": [
                        "Divar advertisement could not be collected."
                    ]
                }
            else:
                result = analyze_single_ad(prepared_ad)

        else:
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
