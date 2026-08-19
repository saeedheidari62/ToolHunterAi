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


def _normalize_market_city(engine, city):
    normalizer = getattr(engine, "_normalize_city", None)
    if callable(normalizer):
        return normalizer(city)
    aliases = {
        "تهران": "tehran", "tehran": "tehran",
        "کرج": "karaj", "karaj": "karaj",
        "مشهد": "mashhad", "mashhad": "mashhad",
        "اصفهان": "isfahan", "isfahan": "isfahan",
        "شیراز": "shiraz", "shiraz": "shiraz",
        "تبریز": "tabriz", "tabriz": "tabriz",
        "قم": "qom", "qom": "qom",
    }
    return aliases.get(str(city or "").strip().lower(), "")


def get_dynamic_market_data(tool_name, city="tehran", variant=None):
    city_slug = _normalize_market_city(divar_search_engine, city)
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
        sample_count = int(market_data.get("sample_count", 0) or 0)
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
        "analysis": ad_analysis["reasons"],
        "image_file": image_file,
        "image_urls": image_urls or [],
    }


# analyze_single_ad and remaining routes intentionally stay unchanged.
