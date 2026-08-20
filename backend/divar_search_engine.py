import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .market_price_engine import MarketPriceEngine


class DivarSearchEngine:

    CITY_SLUGS = {
        "تهران": "tehran", "tehran": "tehran",
        "کرج": "karaj", "karaj": "karaj",
        "مشهد": "mashhad", "mashhad": "mashhad",
        "اصفهان": "isfahan", "isfahan": "isfahan",
        "شیراز": "shiraz", "shiraz": "shiraz",
        "تبریز": "tabriz", "tabriz": "tabriz",
        "قم": "qom", "qom": "qom",
    }

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "KHTML, like Gecko "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
            "Referer": "https://divar.ir/",
        }
        self.project_root = Path(__file__).resolve().parent.parent
        self.tools_index_path = self.project_root / "knowledge_base" / "tools" / "tools_index.json"
        self._tool_index_cache = None
        self._tool_index_mtime = None

    def _load_tool_index(self):
        try:
            current_mtime = self.tools_index_path.stat().st_mtime_ns
        except OSError:
            current_mtime = None
        if self._tool_index_cache is not None and current_mtime == self._tool_index_mtime:
            return self._tool_index_cache
        try:
            with self.tools_index_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError, TypeError):
            data = {"tools": []}
        self._tool_index_cache = data if isinstance(data, dict) else {"tools": []}
        self._tool_index_mtime = current_mtime
        return self._tool_index_cache

    @staticmethod
    def _normalize_text(text):
        text = str(text or "").lower()
        text = text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
        text = text.replace("–", "-").replace("—", "-")
        text = text.replace("ي", "ی").replace("ك", "ک")
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _compact(text):
        return re.sub(r"[^a-z0-9آ-ی]+", "", text)

    def _resolve_tool_name(self, tool_name):
        value = str(tool_name or "").strip()
        if not value:
            return ""
        normalized = self._normalize_text(value).replace("_", " ")
        for tool in self._load_tool_index().get("tools", []):
            if not isinstance(tool, dict):
                continue
            candidates = [tool.get("id"), tool.get("name")]
            candidates.extend(tool.get("aliases") or [])
            for candidate in candidates:
                candidate = str(candidate or "").strip()
                if candidate and self._normalize_text(candidate).replace("_", " ") == normalized:
                    return str(tool.get("name") or value).strip()
        return value

    def build_query(self, tool_name, variant=None, aliases=None):
        query = self._resolve_tool_name(tool_name)
        if not query and aliases:
            query = str(aliases[0]).strip()
        if not query:
            return ""
        if variant and variant != "BASE":
            query = f"{query} {variant}"
        return query

    def _normalize_city(self, city):
        value = self._normalize_text(city).strip()
        return self.CITY_SLUGS.get(value, "")

    def search(self, city, query, variant=None, aliases=None):
        city = self._normalize_city(city)
        query = self.build_query(query, variant, aliases)
        if not city or not query:
            return {"results": [], "search_url": "", "error": "INVALID_SEARCH_INPUT"}
        url = f"https://divar.ir/s/{city}?q={requests.utils.quote(query)}"
        try:
            response = requests.get(url, headers=self.headers, timeout=20, allow_redirects=True)
            response.raise_for_status()
        except requests.RequestException as exc:
            return {"results": [], "search_url": url, "error": "MARKET_FETCH_FAILED", "details": str(exc)}
        return self.parse_results(response.text, url)

    def filter_results(self, results, tool_name, variant=None):
        if not tool_name:
            return results

        normalized_tool = self._normalize_text(self._resolve_tool_name(tool_name))
        tokens = re.findall(r"[a-z0-9]+", normalized_tool)
        model_tokens = [token for token in tokens if any(char.isdigit() for char in token)]
        if not model_tokens:
            return results

        aliases = []
        normalized_lookup = normalized_tool.replace("_", " ")
        for tool in self._load_tool_index().get("tools", []):
            if not isinstance(tool, dict):
                continue
            name = self._normalize_text(tool.get("name", "")).replace("_", " ")
            if name == normalized_lookup:
                aliases = [str(alias) for alias in (tool.get("aliases") or []) if alias]
                break

        match_terms = [normalized_tool] + aliases
        match_compacts = [self._compact(self._normalize_text(term)) for term in match_terms]
        match_compacts = [term for term in match_compacts if any(char.isdigit() for char in term)]

        filtered = []
        for item in results:
            title = self._normalize_text(item.get("title", ""))
            compact_title = self._compact(title)
            model_match = all(token in title or token in compact_title for token in model_tokens)
            alias_match = any(term and term in compact_title for term in match_compacts)
            if not (model_match or alias_match):
                continue
            if variant and variant != "BASE":
                normalized_variant = self._normalize_text(variant)
                compact_variant = self._compact(normalized_variant)
                if compact_variant and compact_variant not in compact_title:
                    continue
            if item.get("price") is None:
                continue
            filtered.append(item)
        return filtered

    def get_market_prices(self, search_result):
        prices = []
        for item in search_result.get("results", []):
            try:
                price = float(item.get("price"))
            except (TypeError, ValueError):
                continue
            if price > 0:
                prices.append(price)
        return MarketPriceEngine().calculate(prices)

    def extract_price(self, title):
        if not title:
            return None
        match = re.search(r"([0-9۰-۹][0-9۰-۹,\.\s]*)\s*تومان", title)
        if not match:
            return None
        value = match.group(1).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
        value = value.replace(",", "").replace(".", "").replace(" ", "")
        try:
            price = int(value)
        except ValueError:
            return None
        return price if price >= 100000 else None

    def parse_results(self, html, search_url=""):
        soup = BeautifulSoup(html, "html.parser")
        results = []
        seen = set()
        for link in soup.find_all("a", href=True):
            title = link.get_text(" ", strip=True)
            if not title:
                continue
            href = link.get("href", "")
            if href.startswith("/"):
                href = "https://divar.ir" + href
            href = href.split("?")[0]
            if "/v/" not in href or href in seen:
                continue
            seen.add(href)
            results.append({"title": title, "price": self.extract_price(title), "url": href})
        return {"results": results, "search_url": search_url}
