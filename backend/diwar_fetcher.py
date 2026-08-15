import json
import re
import requests
from bs4 import BeautifulSoup


class DiwarFetcher:

    def fetch(self, url):
        html = requests.get(
            url,
            timeout=15
        ).text

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        state = self._extract_state(html)

        title = soup.find("h1")
        title = (
            title.get_text(" ", strip=True)
            if title else ""
        )

        description = self._extract_description(soup)

        image_urls = self._extract_image_urls(html)

        return {
            "url": url,
            "title": title,
            "description": description,
            "price": state.get("price", 0),
            "seller_type": state.get(
                "business_type",
                "unknown"
            ),
            "condition": state.get(
                "status",
                "unknown"
            ),
            "brand_model": state.get(
                "brand_model",
                ""
            ),
            "category": state.get(
                "category",
                ""
            ),
            "city": state.get(
                "city",
                ""
            ),
            "district": state.get(
                "district",
                ""
            ),
            "image_count": state.get(
                "image_count",
                0
            ),
            "image_urls": image_urls
        }

    def _extract_state(self, html):

        result = {}

        for key in [
            "business_type",
            "status",
            "price",
            "brand_model",
            "category",
            "city",
            "district",
            "image_count"
        ]:
            pattern = (
                r'"' + key +
                r'"\s*:\s*'
                r'(".*?"|-?\d+)'
            )

            match = re.search(
                pattern,
                html
            )

            if match:
                value = match.group(1)

                if value.startswith('"'):
                    value = json.loads(value)

                else:
                    value = int(value)

                result[key] = value

        return result

    def _extract_image_urls(self, html):

        urls = re.findall(
            r'https?[^"\\ ]+',
            html
        )

        image_urls = []

        for url in urls:

            if "/static/photo/neda/webp_post/" not in url:
                continue

            if url not in image_urls:
                image_urls.append(url)

        return image_urls

    def _extract_description(self, soup):

        h = soup.find(
            "h2",
            string=lambda x:
            x and "توضیحات" in x
        )

        if not h:
            return ""

        p = h.parent.parent.parent.find_next("p")

        return (
            p.get_text(" ", strip=True)
            if p else ""
        )
