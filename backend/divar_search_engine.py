import re
import requests

from .market_price_engine import MarketPriceEngine
from bs4 import BeautifulSoup


class DivarSearchEngine:

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
            "Referer": "https://divar.ir/",
        }

    def build_query(self, tool_name, variant=None):
        base_query = str(tool_name or "").strip()

        if not base_query:
            return ""

        if (
            tool_name == "bosch_gbh_2_26"
            and variant in {"DFR", "DRE"}
        ):
            return f"Bosch GBH 2-26 {variant}"

        return base_query

    def search(self, city, query, variant=None):
        query = self.build_query(
            query,
            variant
        )

        url = (
            f"https://divar.ir/s/{city}"
            f"?q={requests.utils.quote(query)}"
        )

        response = requests.get(
            url,
            headers=self.headers,
            timeout=20,
            allow_redirects=True
        )

        response.raise_for_status()

        return self.parse_results(
            response.text,
            url
        )


    def filter_results(self, results, tool_name, variant=None):
        if not tool_name:
            return results

        normalized_tool = tool_name.lower()

        tokens = re.findall(
            r"[a-z0-9]+",
            normalized_tool
        )

        model_tokens = [
            token
            for token in tokens
            if any(char.isdigit() for char in token)
        ]

        if not model_tokens:
            return results

        filtered = []

        for item in results:
            title = (
                item.get("title", "")
                .lower()
            )

            if not all(
                token in title
                for token in model_tokens
            ):
                continue

            if variant in ("DFR", "DRE"):
                variant_pattern = (
                    rf"\bgbh[\s-]*2[\s-]*26[\s-]*"
                    rf"{variant.lower()}\b"
                )

                if not re.search(
                    variant_pattern,
                    title
                ):
                    continue

            if item.get("price") is None:
                continue

            filtered.append(item)

        return filtered

    def get_market_prices(self, search_result):
        prices = []

        for item in search_result.get("results", []):
            price = item.get("price")

            if price is None:
                continue

            try:
                price = float(price)
            except (TypeError, ValueError):
                continue

            if price > 0:
                prices.append(price)

        engine = MarketPriceEngine()

        return engine.calculate(prices)

    def extract_price(self, title):
        if not title:
            return None

        match = re.search(
            r'([0-9۰-۹][0-9۰-۹,\.\s]*)\s*تومان',
            title
        )

        if not match:
            return None

        value = match.group(1)

        translation = str.maketrans(
            "۰۱۲۳۴۵۶۷۸۹",
            "0123456789"
        )

        value = value.translate(
            translation
        )

        value = (
            value
            .replace(",", "")
            .replace(".", "")
            .replace(" ", "")
        )

        try:
            price = int(value)
        except ValueError:
            return None

        if price < 100000:
            return None

        return price

    def parse_results(self, html, search_url=""):
        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        results = []

        links = soup.find_all(
            "a",
            href=re.compile(r"/v/")
        )

        seen = set()

        for link in links:
            href = link.get("href", "")

            if not href:
                continue

            if href.startswith("/"):
                url = "https://divar.ir" + href
            else:
                url = href

            url = url.split("?")[0]

            if url in seen:
                continue

            seen.add(url)

            title = link.get_text(
                " ",
                strip=True
            )

            if not title:
                continue

            price = self.extract_price(title)

            results.append({
                "title": title,
                "url": url,
                "price": price
            })

        return {
            "query": search_url,
            "status": "success",
            "results": results
        }
