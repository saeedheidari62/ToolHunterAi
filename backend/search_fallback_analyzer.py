from .ad_analyzer import analyze_ad
from .collector import AdCollector
from .decision_engine import make_decision
from .opportunity_engine import OpportunityEngine


class SearchFallbackAnalyzer:
    """Analyze search-result evidence when a listing page cannot be fetched."""

    def __init__(self):
        self.collector = AdCollector()
        self.opportunity_engine = OpportunityEngine()

    def analyze(self, candidate, tool_id, city):
        title = str(candidate.get("title", "")).strip()
        price = candidate.get("price")
        if not title or price in (None, "", 0):
            return None

        ad = self.collector.collect(
            title=title,
            description="",
            price=price,
            seller_type="unknown",
            testing=False,
            warranty=False,
            condition="unknown",
            url=candidate.get("url", ""),
            city=city,
            image_count=0,
            image_urls=[],
        )
        ad_analysis = analyze_ad(ad)
        decision = make_decision({
            "tool_name": tool_id,
            "asking_price": ad["price"],
            "market_data": None,
            "has_test": False,
            "has_warranty": False,
            "description": "",
            "ad_score": ad_analysis["ad_score"],
            "analysis": ad_analysis["analysis"],
            "image_urls": [],
            "image_file": None,
        })
        result = dict(decision)
        result.update({
            "tool": tool_id,
            "title": ad["title"],
            "url": ad["url"],
            "city": city,
            "variant": None,
            "market_data": None,
            "market_source": "knowledge_base",
            "data_completeness": "PARTIAL_SEARCH_EVIDENCE",
            "analysis_source": "search_result_fallback",
            "fetch_warning": "Listing page could not be fetched; decision uses search-result title and price only.",
        })
        result["opportunity_score"] = self.opportunity_engine.score(result)
        result["opportunity_status"] = (
            "OPPORTUNITY" if result["opportunity_score"] >= 60
            else "WATCH" if result["opportunity_score"] >= 40
            else "LOW_VALUE"
        )
        if result.get("decision") == "BUY":
            result["decision"] = "REVIEW"
            result["decision_reason"] = "Listing-page verification failed, so BUY is blocked until the advertisement can be fetched and verified."
            result["next_action"] = "Retry listing fetch and verify description, seller, testing, warranty, and images before purchase."
        return result
