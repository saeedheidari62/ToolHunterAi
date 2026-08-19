import json
import uuid
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, request

from .collector import AdCollector
from .diwar_collector import DiwarCollector
from .diwar_fetcher import DiwarFetcher
from .decision_engine import make_decision
from .ad_analyzer import analyze_ad
from .tool_matcher import ToolMatcher
from .tool_variant_matcher import ToolVariantMatcher
from .multi_tool_analyzer import MultiToolAnalyzer
from .rank_engine import RankEngine
from .decision_explainer import DecisionExplainer
from .history_manager import save_history, get_history, get_history_by_id
from .ad_normalizer import AdNormalizer
from .divar_search_engine import DivarSearchEngine
from .ai.tool_resolver import AIToolResolver
from .ai.tool_discovery import AIToolDiscovery
from .ai.tool_candidate_validator import ToolCandidateValidator
from .ai.tool_candidate_promoter import ToolCandidatePromoter

app = Flask(__name__)
collector = AdCollector()
diwar_collector = DiwarCollector()
diwar_fetcher = DiwarFetcher()
matcher = ToolMatcher()
variant_matcher = ToolVariantMatcher()
multi_tool_analyzer = MultiToolAnalyzer()
ranker = RankEngine()
explainer = DecisionExplainer()
normalizer = AdNormalizer()
divar_search_engine = DivarSearchEngine()
ai_tool_resolver = AIToolResolver()
ai_tool_discovery = AIToolDiscovery()
ai_tool_candidate_validator = ToolCandidateValidator(divar_search_engine)
ai_tool_candidate_promoter = ToolCandidatePromoter()

_PREPARED_AD_CACHE = {}
_PREPARED_AD_CACHE_TTL_SECONDS = 300

ERROR_CODES = {
    "FETCH_FAILED": "Divar advertisement could not be fetched.",
    "FETCH_INCOMPLETE": "Divar advertisement data is incomplete.",
    "COLLECTION_FAILED": "Divar advertisement could not be collected.",
    "INVALID_AD": "Invalid advertisement data.",
    "TOOL_NOT_RECOGNIZED": "Tool not recognized.",
    "MULTIPLE_TOOLS": "Multiple tools detected.",
}


def _error(code, **extra):
    payload = {"error": code, "message": ERROR_CODES.get(code, code)}
    payload.update(extra)
    return payload


def create_analysis_id():
    return str(uuid.uuid4())


def create_timestamp():
    return datetime.now(timezone.utc).isoformat()


def _get_cached_prepared_ad(url):
    cached = _PREPARED_AD_CACHE.get(url)
    if not cached:
        return None
    cached_at, ad = cached
    if time.monotonic() - cached_at > _PREPARED_AD_CACHE_TTL_SECONDS:
        _PREPARED_AD_CACHE.pop(url, None)
        return None
    return dict(ad)


def prepare_ad(ad):
    if not isinstance(ad, dict) or "url" not in ad:
        return ad
    url = str(ad.get("url", "")).strip()
    if not url:
        return ad
    cached_ad = _get_cached_prepared_ad(url)
    if cached_ad is not None:
        return cached_ad
    diagnostics = {"url": url, "fetch_attempts": 0, "last_stage": "fetch", "title_found": False, "description_found": False, "price_found": False, "image_count": 0}
    for attempt in range(3):
        diagnostics["fetch_attempts"] = attempt + 1
        try:
            fetched_ad = diwar_fetcher.fetch(url)
        except Exception as exc:
            diagnostics["last_stage"] = "fetch"
            diagnostics["fetch_exception"] = type(exc).__name__
            if attempt < 2:
                time.sleep(0.5)
                continue
            return {"_prepare_error": "FETCH_FAILED", "_prepare_diagnostics": diagnostics}
        if not isinstance(fetched_ad, dict):
            if attempt < 2:
                time.sleep(0.5)
                continue
            return {"_prepare_error": "FETCH_FAILED", "_prepare_diagnostics": diagnostics}
        diagnostics["title_found"] = bool(str(fetched_ad.get("title", "")).strip())
        diagnostics["description_found"] = bool(str(fetched_ad.get("description", "")).strip())
        diagnostics["price_found"] = bool(fetched_ad.get("price", 0))
        diagnostics["image_count"] = fetched_ad.get("image_count", 0)
        if not diagnostics["title_found"]:
            if attempt < 2:
                time.sleep(0.5)
                continue
            return {"_prepare_error": "FETCH_INCOMPLETE", "_prepare_diagnostics": diagnostics}
        try:
            diagnostics["last_stage"] = "collect"
            collected_ad = diwar_collector.collect(fetched_ad)
        except Exception as exc:
            diagnostics["collection_exception"] = type(exc).__name__
            collected_ad = None
        if isinstance(collected_ad, dict):
            _PREPARED_AD_CACHE[url] = (time.monotonic(), dict(collected_ad))
            return collected_ad
        if attempt < 2:
            time.sleep(0.5)
            continue
        return {"_prepare_error": "COLLECTION_FAILED", "_prepare_diagnostics": diagnostics}
    return {"_prepare_error": "FETCH_FAILED", "_prepare_diagnostics": diagnostics}


def get_dynamic_market_data(tool_name, city="tehran", variant=None):
    city_map = {"تهران": "tehran", "teران": "tehran", "tehran": "tehran", "کرج": "karaj", "karaj": "karaj", "مشهد": "mashhad", "mashhad": "mashhad", "اصفهان": "isfahan", "isfahan": "isfahan", "شیراز": "shiraz", "shiraz": "shiraz", "تبریز": "tabriz", "tabriz": "tabriz"}
    city_key = str(city or "").strip().lower()
    city_slug = city_map.get(city_key)
    if not city_slug:
        return None
    try:
        search_result = divar_search_engine.search(city_slug, tool_name, variant=variant)
        filtered = divar_search_engine.filter_results(search_result.get("results", []), tool_name, variant)
        if not filtered:
            return None
        market_data = divar_search_engine.get_market_prices({"results": filtered})
        if not market_data.get("valid"):
            return None
        sample_count = market_data.get("sample_count", 0)
        if sample_count >= 3:
            market_data["confidence"] = "HIGH"
        elif sample_count >= 2:
            market_data["confidence"] = "MEDIUM"
        elif sample_count == 1:
            market_data["confidence"] = "LOW"
        else:
            return None
        market_data["variant"] = variant
        market_data["city"] = city_slug
        market_data["source"] = "dynamic_divar"
        return market_data
    except Exception:
        return None


def _promote_discovered_candidate(discovery, validation, collected_ad):
    if not isinstance(validation, dict) or validation.get("status") != "VALIDATED":
        return None
    candidate = dict(discovery or {})
    candidate.update(validation)
    candidate["status"] = validation.get("status")
    candidate["description"] = collected_ad.get("description", "")
    candidate["title"] = collected_ad.get("title", "")
    candidate["city"] = collected_ad.get("city")
    candidate["technical_data"] = candidate.get("technical_data", discovery.get("technical_data", {}))
    candidate["technical_sources"] = candidate.get("technical_sources", discovery.get("technical_sources", []))
    return ai_tool_candidate_promoter.promote(candidate)


def _decision_payload(tool_id, asking_price, collected_ad, ad_analysis, description, market_data=None, image_file=None, image_urls=None):
    return {
        "tool_name": tool_id,
        "asking_price": asking_price or 0,
        "market_data": market_data,
        "has_test": collected_ad["has_test"],
        "has_warranty": collected_ad["has_warranty"],
        "description": description,
        "ad_score": ad_analysis["ad_score"],
        "analysis": ad_analysis["analysis"],
        "image_file": image_file,
        "image_urls": image_urls or [],
    }


def analyze_single_ad(ad):
    ad = prepare_ad(ad)
    if isinstance(ad, dict) and ad.get("_prepare_error"):
        return _error(ad["_prepare_error"], diagnostics=ad.get("_prepare_diagnostics", {}))
    normalized = normalizer.normalize(ad)
    if not normalized["valid"]:
        return _error("INVALID_AD", errors=normalized["errors"])
    ad = normalized["ad"]
    collected_ad = collector.collect(
        title=ad["title"],
        description=ad["description"],
        price=ad["price"],
        seller_type=ad["seller_type"],
        testing=ad.get("testing", False),
        warranty=ad.get("warranty", False),
        condition=ad.get("condition", "used"),
        **{key: ad.get(key) for key in (
            "url", "city", "district", "brand_model", "category",
            "image_count", "image_urls", "image_file"
        ) if key in ad}
    )
    match_text = collected_ad["title"] + " " + collected_ad["description"] + " " + collected_ad.get("brand_model", "")
    tool_ids = matcher.match_all(match_text)
    ai_resolution = None
    if not tool_ids:
        ai_resolution = ai_tool_resolver.resolve(match_text)
        if ai_resolution:
            tool_ids = [ai_resolution["tool_id"]]
    discovery = None
    validation = None
    promotion = None
    if not tool_ids:
        discovery = ai_tool_discovery.discover(match_text)
        if discovery:
            validation = ai_tool_candidate_validator.validate(discovery, city=collected_ad.get("city"))
            promotion = _promote_discovered_candidate(discovery, validation, collected_ad)
            if isinstance(promotion, dict) and promotion.get("status") in {"PROMOTED", "EXISTS"}:
                matcher.reload()
                tool_ids = matcher.match_all(match_text)
                promoted_tool_id = promotion.get("tool_id")
                if not tool_ids and promoted_tool_id:
                    tool_ids = [promoted_tool_id]
                ai_resolution = {"source": "candidate_promotion", "confidence": discovery.get("confidence", 0), "evidence": discovery.get("evidence", [])}
        if not tool_ids:
            return _error("TOOL_NOT_RECOGNIZED", title=collected_ad["title"], matched_tools=[], tool_discovery=discovery, tool_discovery_validation=validation, tool_candidate_promotion=promotion)
    if len(tool_ids) > 1:
        multi_result = multi_tool_analyzer.analyze(collected_ad["description"], tool_ids)
        ad_analysis = analyze_ad(collected_ad)
        individual_results = []
        for item in multi_result["tools"]:
            tool_id = item["tool_id"]
            asking_price = item["asking_price"]
            decision_data = _decision_payload(tool_id, asking_price, collected_ad, ad_analysis, item["text"], image_file=ad.get("image_file"), image_urls=ad.get("image_urls", []))
            decision = make_decision(decision_data)
            individual_results.append({"tool_id": tool_id, "asking_price": asking_price, "decision": decision})
        return {
            "status": "REVIEW",
            "message": ERROR_CODES["MULTIPLE_TOOLS"],
            "title": collected_ad["title"],
            "matched_tools": tool_ids,
            "multi_tool_analysis": multi_result,
            "individual_results": individual_results,
            "decision": "REVIEW",
            "reason": "Multiple tools were detected and each tool was analyzed independently.",
        }
    tool_id = tool_ids[0]
    variant = variant_matcher.detect(collected_ad["title"] + " " + collected_ad["description"], tool_id)
    ad_analysis = analyze_ad(collected_ad)
    market_data = get_dynamic_market_data(tool_id, collected_ad.get("city"), variant)
    decision_data = _decision_payload(tool_id, collected_ad["price"], collected_ad, ad_analysis, collected_ad["description"], market_data=market_data, image_file=ad.get("image_file"), image_urls=ad.get("image_urls", []))
    result = make_decision(decision_data)
    result["has_test"] = collected_ad["has_test"]
    result["has_warranty"] = collected_ad["has_warranty"]
    result["price_status"] = result.get("price_status")
    result["price_difference_percent"] = result.get("price_difference_percent")
    result["ad_score"] = ad_analysis["ad_score"]
    result["tool"] = tool_id
    result["variant"] = variant
    result["title"] = collected_ad["title"]
    result["market_data"] = market_data
    result["market_source"] = (market_data or {}).get("source") if isinstance(market_data, dict) else None
    if discovery is not None:
        result["tool_discovery"] = discovery
        result["tool_discovery_validation"] = validation
        result["tool_candidate_promotion"] = promotion
    if ai_resolution:
        result["ai_tool_resolution"] = ai_resolution
    return result


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "INVALID_REQUEST", "message": "Invalid or missing JSON data."}), 400
    if "ads" not in data:
        return jsonify({"error": "MISSING_ADS", "message": "Field 'ads' is required."}), 400
    ads = data["ads"]
    if not isinstance(ads, list):
        return jsonify({"error": "INVALID_ADS", "message": "Field 'ads' must be a list."}), 400
    if not ads:
        return jsonify({"error": "EMPTY_ADS", "message": "Ads list cannot be empty."}), 400
    results = []
    errors = []
    for index, ad in enumerate(ads):
        result = analyze_single_ad(ad)
        if "error" in result:
            errors.append({"index": index, "error": result})
        else:
            results.append(result)
    if not results:
        return jsonify({"error": "NO_VALID_ADS", "message": "No valid ads could be analyzed.", "errors": errors}), 400
    final = ranker.rank(results)
    explanation = explainer.explain(final["best_choice"], final["ranking"])
    analysis_id = create_analysis_id()
    created_at = create_timestamp()
    analysis_record = {"analysis_id": analysis_id, "created_at": created_at, "service": "ToolHunterAI API", "version": "2.0", "total_ads": final["total_ads"], "best_choice": final["best_choice"], "ranking": final["ranking"], "explanation": explanation, "errors": errors}
    save_history(analysis_record)
    return jsonify({"analysis_id": analysis_id, "created_at": created_at, "service": "ToolHunterAI API", "version": "2.0", "total_ads": final["total_ads"], "best_choice": final["best_choice"], "ranking": final["ranking"], "explanation": explanation, "errors": errors})


@app.route("/history", methods=["GET"])
def history():
    records = get_history()
    return jsonify({"service": "ToolHunterAI API", "total": len(records), "history": records})


@app.route("/history/<analysis_id>", methods=["GET"])
def history_detail(analysis_id):
    record = get_history_by_id(analysis_id)
    if record is None:
        return jsonify({"error": "ANALYSIS_NOT_FOUND", "message": "Analysis not found.", "analysis_id": analysis_id}), 404
    return jsonify({"service": "ToolHunterAI API", "analysis": record})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
