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
from .tool_variant_matcher import ToolVariantMatcher
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
from .ai.tool_resolver import AIToolResolver
from .ai.tool_discovery import AIToolDiscovery

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

    try:
        fetched_ad = diwar_fetcher.fetch(url)
    except Exception:
        return {
            "_prepare_error": "Divar advertisement could not be fetched."
        }

    if not isinstance(fetched_ad, dict):
        return {
            "_prepare_error": "Divar advertisement could not be fetched."
        }

    try:
        collected_ad = diwar_collector.collect(fetched_ad)
    except Exception:
        return {
            "_prepare_error": "Divar advertisement could not be collected."
        }

    if not isinstance(collected_ad, dict):
        return {
            "_prepare_error": "Divar advertisement could not be collected."
        }

    return collected_ad


def get_dynamic_market_data(
    tool_name,
    city="tehran",
    variant=None
):
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
            tool_name,
            variant=variant
        )

        filtered = divar_search_engine.filter_results(
            search_result.get("results", []),
            tool_name,
            variant
        )

        if not filtered:
            return None

        market_data = divar_search_engine.get_market_prices({
            "results": filtered
        })

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
        return market_data

    except Exception:
        return None


def analyze_single_ad(ad):
    ad = prepare_ad(ad)

    if isinstance(ad, dict) and ad.get("_prepare_error"):
        return {
            "error": ad["_prepare_error"]
        }

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
    ai_resolution = None
    tool_discovery = None

    if not tool_ids:
        ai_resolution = ai_tool_resolver.resolve(match_text)
        if ai_resolution:
            tool_ids = [ai_resolution["tool_id"]]

    if not tool_ids:
        tool_discovery = ai_tool_discovery.discover(match_text)
        return {
            "error": "Tool not recognized.",
            "title": collected_ad["title"],
            "matched_tools": [],
            "tool_discovery": tool_discovery
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
                "asking_price": asking_price,
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
            "individual_results": individual_results
        }

    tool_id = tool_ids[0]
    variant = variant_matcher.detect(match_text, tool_id)

    ad_analysis = analyze_ad(collected_ad)
    market_data = get_dynamic_market_data(
        tool_id,
        city=collected_ad.get("city", "tehran"),
        variant=variant
    )

    decision_data = {
        "tool_name": tool_id,
        "asking_price": collected_ad["price"],
        "has_test": collected_ad["has_test"],
        "has_warranty": collected_ad["has_warranty"],
        "description": collected_ad["description"],
        "ad_score": ad_analysis["ad_score"],
        "analysis": ad_analysis["analysis"],
        "image_file": ad.get("image_file"),
        "image_urls": ad.get("image_urls", []),
        "market_data": market_data,
    }

    decision = make_decision(decision_data)

    result = dict(decision)
    result["tool"] = tool_id
    result["variant"] = variant
    result["title"] = collected_ad["title"]
    if ai_resolution:
        result["ai_tool_resolution"] = ai_resolution

    return result
