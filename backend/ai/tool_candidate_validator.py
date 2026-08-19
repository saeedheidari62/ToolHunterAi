from backend.market_price_engine import MarketPriceEngine


class ToolCandidateValidator:
    """Validate discovered tool candidates before any Knowledge Base promotion."""
    CITY_ALIASES = {"تهران":"tehran","tehran":"tehran","کرج":"karaj","karaj":"karaj","مشهد":"mashhad","mashhad":"mashhad","اصفهان":"isfahan","isfahan":"isfahan","شیراز":"shiraz","shiraz":"shiraz","تبریز":"tabriz","tabriz":"tabriz","قم":"qom","qom":"qom"}

    def __init__(self, search_engine, min_samples=2):
        self.search_engine = search_engine
        self.market_engine = MarketPriceEngine()
        self.min_samples = int(min_samples)

    def _normalize_city(self, city):
        return self.CITY_ALIASES.get(str(city or "tehran").strip().lower())

    @staticmethod
    def _confidence_from_count(count):
        if count >= 3: return "HIGH"
        if count >= 2: return "MEDIUM"
        if count == 1: return "LOW"
        return "NONE"

    def validate(self, candidate, city=None):
        if not isinstance(candidate, dict): return None
        brand = str(candidate.get("brand", "")).strip(); model = str(candidate.get("model", "")).strip(); variant = str(candidate.get("variant", "")).strip()
        try: confidence = float(candidate.get("confidence", 0))
        except (TypeError, ValueError): confidence = 0
        if not brand or not model: return {"status":"REJECTED","reason":"Brand and model are required."}
        if confidence < 0.80: return {"status":"REJECTED","reason":"Discovery confidence is below validation threshold."}
        city_slug = self._normalize_city(city)
        base = {"brand":brand,"model":model,"variant":variant,"confidence":confidence,"evidence":candidate.get("evidence",[]),"technical_data":candidate.get("technical_data",candidate.get("technical",{})),"technical_sources":candidate.get("technical_sources",[]),"city":city_slug,"query":f"{brand} {model}"}
        if not city_slug: return {**base,"status":"UNVERIFIED","market_sample_count":0,"market_data":None,"reason":"A supported marketplace city is required for market validation."}
        try:
            try: search_result = self.search_engine.search(city_slug, base["query"], variant=variant or None)
            except TypeError: search_result = self.search_engine.search(city_slug, base["query"])
            results = search_result.get("results",[]) if isinstance(search_result,dict) else []
        except Exception: return {**base,"status":"UNVERIFIED","market_sample_count":0,"market_data":None,"reason":"Market validation search failed."}
        model_key = "".join(ch.lower() for ch in model if ch.isalnum())
        matched = [item for item in results if model_key and model_key in "".join(ch.lower() for ch in str(item.get("title","")) if ch.isalnum()) and item.get("price") is not None]
        if not matched: return {**base,"status":"UNVERIFIED","market_sample_count":0,"market_data":None,"reason":"Insufficient marketplace evidence to validate the candidate."}
        try:
            if callable(getattr(self.search_engine,"get_market_prices",None)): market_result = self.search_engine.get_market_prices({"results":matched})
            else: market_result = self.market_engine.calculate([item.get("price") for item in matched])
        except Exception: market_result = self.market_engine.calculate([item.get("price") for item in matched])
        if not isinstance(market_result,dict) or not market_result.get("valid"):
            return {**base,"status":"UNVERIFIED","market_sample_count":0,"market_data":None,"reason":"Marketplace prices could not be validated."}
        try: reported_count = int(market_result.get("sample_count",0) or 0)
        except (TypeError,ValueError): reported_count = 0
        try: search_count = int(search_result.get("sample_count",0) or 0) if isinstance(search_result,dict) else 0
        except (TypeError,ValueError): search_count = 0
        count = max(reported_count, search_count, len(matched))
        confidence_level = self._confidence_from_count(count)
        market_data = {"valid":True,"used_price_min":market_result.get("min_price"),"used_price_max":market_result.get("max_price"),"median_price":market_result.get("median_price"),"min_price":market_result.get("min_price"),"max_price":market_result.get("max_price"),"sample_count":count,"price_confidence":confidence_level,"confidence":confidence_level,"sources":["divar"],"city":city_slug,"variant":variant}
        status = "VALIDATED" if count >= self.min_samples else "UNVERIFIED"
        return {**base,"status":status,"market_sample_count":count,"market_data":market_data,"reason":"Candidate model was found in multiple marketplace listings." if status == "VALIDATED" else "Insufficient marketplace evidence to validate the candidate."}
