import json
import re
import requests
from bs4 import BeautifulSoup


class DiwarFetcher:

    def fetch(self, url):

        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
                "Referer": "https://divar.ir/",
            },
            timeout=20,
            allow_redirects=True
        )

        response.raise_for_status()
        html = response.text

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        state = self._extract_state(html)

        title = ""

        product_match = re.search(
            r'"city_persian"\s*:\s*"[^"]*"'
            r'.{0,500}?'
            r'"name"\s*:\s*"([^"]+)"'
            r'.{0,300}?'
            r'"offers"\s*:',
            html
        )

        if product_match:
            title = product_match.group(1)

        if not title:
            title_tag = soup.find("h1")

            title = (
                title_tag.get_text(
                    " ",
                    strip=True
                )
                if title_tag
                else ""
            )

        description = self._extract_description(
            soup
        )

        image_urls = self._extract_image_urls(
            html
        )

        seller_type = state.get(
            "business_type",
            ""
        )

        condition = state.get(
            "status",
            "unknown"
        )

        if not seller_type:

            seller_type = self._detect_seller_type(
                title,
                description
            )

        if not condition:

            condition = "unknown"

        raw_price = state.get(
            "price",
            0
        )

        try:

            price = int(raw_price)

        except (
            TypeError,
            ValueError
        ):

            price = 0

        if price <= 0:

            offer_match = re.search(
                r'"offers"\s*:\s*\{[^}]*'
                r'"price"\s*:\s*"?(\d+)"?',
                html
            )

            if offer_match:

                try:
                    price = int(
                        offer_match.group(1)
                    )
                except (
                    TypeError,
                    ValueError
                ):
                    price = 0

        return {
            "url": url,
            "title": title,
            "description": description,
            "price": price,
            "seller_type": seller_type,
            "condition": condition,
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

    def _detect_seller_type(
        self,
        title,
        description
    ):

        text = (
            (title or "")
            + " "
            + (description or "")
        ).lower()

        # -------------------------------------------------
        # Strong business signals
        # -------------------------------------------------

        business_phrases = [
            "فروشگاه",
            "ابزارفروشی",
            "فروش انواع",
            "خرید حضوری",
            "خرید غیرحضوری",
            "ارسال به سراسر کشور",
            "پرداخت درب منزل",
            "جهت مشاوره",
            "با ما تماس",
            "تماس بگیرید",
            "مشاوره رایگان",
            "ضمانت",
            "گارانتی",
            "پلاک",
            "پاساژ",
            "مغازه",
            "فروشنده",
            "ثبت سفارش",
            "استعلام قیمت",
            "قیمت روز"
        ]

        business_score = 0

        for phrase in business_phrases:

            if phrase in text:

                business_score += 1

        # -------------------------------------------------
        # Personal seller signals
        # -------------------------------------------------

        personal_phrases = [
            "شخصی",
            "مصرف شخصی",
            "برای خودم",
            "وسیله شخصی",
            "استفاده شخصی",
            "به دلیل نیاز مالی",
            "به دلیل جابجایی",
            "اسباب کشی",
            "فروش فوری"
        ]

        personal_score = 0

        for phrase in personal_phrases:

            if phrase in text:

                personal_score += 1

        # -------------------------------------------------
        # Decision
        # -------------------------------------------------

        if business_score >= 2:

            return "business"

        if personal_score >= 2:

            return "personal"

        if business_score == 1:

            return "business"

        if personal_score == 1:

            return "personal"

        return "unknown"

    def _extract_state(
        self,
        html
    ):

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
                r'"'
                + key
                + r'"\s*:\s*'
                r'(".*?"|-?\d+)'
            )

            match = re.search(
                pattern,
                html
            )

            if match:

                value = match.group(1)

                if value.startswith('"'):

                    try:

                        value = json.loads(
                            value
                        )

                    except (
                        json.JSONDecodeError
                    ):

                        value = value.strip(
                            '"'
                        )

                else:

                    try:

                        value = int(value)

                    except ValueError:

                        continue

                result[key] = value

        return result

    def _extract_image_urls(
        self,
        html
    ):

        urls = re.findall(
            r'https?[^"\\ ]+',
            html
        )

        image_urls = []

        for url in urls:

            if (
                "/static/photo/neda/webp_post/"
                not in url
            ):

                continue

            if url not in image_urls:

                image_urls.append(
                    url
                )

        return image_urls

    def _extract_description(
        self,
        soup
    ):

        h = soup.find(
            "h2",
            string=lambda x:
            x and "توضیحات" in x
        )

        if not h:

            return ""

        p = (
            h.parent
            .parent
            .parent
            .find_next("p")
        )

        return (
            p.get_text(
                " ",
                strip=True
            )
            if p
            else ""
        )