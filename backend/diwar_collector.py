import re


class DiwarCollector:

    def collect(self, raw_ad):
        if not isinstance(raw_ad, dict):
            return None

        title = self.clean_text(raw_ad.get("title"))
        description = self.clean_text(raw_ad.get("description", ""))

        if not title:
            return None

        return {
            "title": title,
            "description": description,
            "price": self.clean_price(raw_ad.get("price", 0)),
            "seller_type": self.clean_seller_type(
                raw_ad.get("seller_type", "unknown")
            ),
            "testing": self.get_testing(raw_ad, title, description),
            "warranty": self.clean_bool(raw_ad.get("warranty", False)),
            "condition": self.clean_condition(
                raw_ad.get("condition", "used")
            ),
            "image_count": raw_ad.get("image_count", 0),
            "image_urls": raw_ad.get("image_urls", []),
            "brand_model": self.clean_text(
                raw_ad.get("brand_model", "")
            ),
            "image_file": raw_ad.get("image_file")
        }

    def get_testing(self, raw_ad, title, description):
        if "testing" in raw_ad and raw_ad["testing"] is not None:
            return self.clean_bool(raw_ad["testing"])

        text = f"{title} {description}".lower()

        negative = [
            "بدون تست",
            "تست ندارد",
            "امکان تست ندارد",
            "فاقد تست"
        ]

        positive = [
            "امکان تست",
            "تست حضوری",
            "مهلت تست",
            "با تست",
            "تست دارد"
        ]

        if any(x in text for x in negative):
            return False

        return any(x in text for x in positive)

    def clean_text(self, value):
        if value is None:
            return ""

        return " ".join(str(value).split())

    def clean_price(self, value):
        if isinstance(value, bool):
            return 0

        try:
            text = str(value).replace(",", "").replace(" ", "")
            nums = re.findall(r"\d+", text)

            if not nums:
                return 0

            return int("".join(nums))

        except (ValueError, TypeError):
            return 0

    def clean_bool(self, value):
        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return value != 0

        text = str(value).strip().lower()

        return text in (
            "true",
            "1",
            "yes",
            "y",
            "on",
            "بله",
            "بلی"
        )

    def clean_seller_type(self, value):
        text = str(value).strip().lower()

        if text in (
            "personal",
            "person",
            "individual",
            "شخصی",
            "فردی"
        ):
            return "Personal"

        if text in (
            "business",
            "company",
            "shop",
            "dealer",
            "کسب‌وکار",
            "کسب و کار",
            "فروشگاه",
            "شرکتی",
            "premium-panel"
        ):
            return "Business"

        return "Unknown"

    def clean_condition(self, value):
        text = str(value).strip().lower()

        if text in ("new", "نو"):
            return "New"

        if text in (
            "used",
            "second hand",
            "دست دوم",
            "کارکرده"
        ):
            return "Used"

        return "Used"
