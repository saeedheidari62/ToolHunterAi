import re
import requests

from bs4 import BeautifulSoup

from .market_price_engine import MarketPriceEngine


class DivarSearchEngine:

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
            "Referer": "https://divar.ir/",
        }

    def build_query(self, tool_name, variant=None, aliases=None):
        """Build a human-readable marketplace query from a tool id/name."""
        base_query = str(tool_name or "").strip()
        if not base_query:
            return ""

        known_names = {
            "bosch_gbh_2_26": "Bosch GBH 2-26",
            "makita_hr2470": "Makita HR2470",
            "bosch_gsh500": "Bosch GSH500",
            "dewalt_d25810": "DeWalt D25810",
            "bosch_p10": "Bosch P10",
            "bosch_pss280": "Bosch PSS280",
            "makita_3600b": "Makita 3600B",
        }
        query = known_names.get(base_query.lower(), base_query)

        if variant and variant != "BASE":
            query = f"{query} {variant}"

        return query

    def search(self, city, query, variant=None, aliases=None):
        query = self.build_query(query, variant, aliases)
        if not city or not query:
            return {"results": [], "search_url": "", "error": "INVALID_SEARCH_INPUT"}

        url = (
            f"https://divar.ir/s/{city}"
            f"?q={requests.utils.quote(query)}"
        )

        response = requests.get(
            url,
            headers=self.headers,
            timeout=20,
            allow_redirects=True,
        )
        response.raise_for_status()
        return self.parse_results(response.text, url)

    def filter_results(self, results, tool_name, variant=None):
        if not tool_name:
            return results

        normalized_tool = tool_name.lower()
        tokens = re.findall(r"[a-z0-9]+", normalized_tool)
        model_tokens = [
            token for token in tokens
            if any(char.isdigit() for char in token)
        ]

        if not model_tokens:
            return results

        filtered = []
        for item in results:
            title = str(item.get("title", "")).lower()
            if not all(token in title for token in model_tokens):
                continue

            if variant and variant != "BASE":
                variant_pattern = (
                    rf"\bgbh[\s-]*2[\s-]*26[\s-]*"
                    rf"{re.escape(variant.lower())}\b"
                )
                if tool_name == "bosch_gbh_2_26" and not re.search(variant_pattern, title):
                    continue

            if item.get("price") is None:
                continue
            filtered.append(item)

        return filtered

    def get_market_prices(self, search_result):
        prices = []
        for item in search_result.get("results", []):
            price = item.get("price")
            try:
                price = float(price)
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
        value = match.group(1).translate(
            str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
        )
        value = value.replace(",", "").replace(".", "").replace(" ", "")
        try:
            price = int(value)
        except ValueError:
            return None
        return price if price >= 100000 else None

    def parse_results(self, html, search_url=""):
        soup = BeautifulSoup(html, "html.parser")
        results = []

        for link in soup.find_all("a", href=True):
            title = link.get_text(" ", strip=True)
            if not title:
                continue

            price = self.extract_price(title)
            href = link.get("href", "")
            if href.startswith("/"):
                href = "https://divar.ir" + href

            results.append({
                "title": title,
                "price": price,
                "url": href,
            })

        return {"results": results, "search_url": search_url}
