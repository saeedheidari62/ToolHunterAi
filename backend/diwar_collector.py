import re


class DiwarCollector:
    """
    Normalize raw advertisement data from Divar
    into the standard ToolHunterAI advertisement format.
    """

    def __init__(self):
        pass

    def collect(self, raw_ad):
        if not isinstance(raw_ad, dict):
            return None

        title = self.clean_text(
            raw_ad.get("title")
        )

        description = self.clean_text(
            raw_ad.get("description", "")
        )

        if not title:
            return None

        price = self.clean_price(
            raw_ad.get("price", 0)
        )

        seller_type = self.clean_seller_type(
            raw_ad.get("seller_type", "unknown")
        )

        testing = self.clean_bool(
            raw_ad.get("testing", False)
        )

        warranty = self.clean_bool(
            raw_ad.get("warranty", False)
        )

        condition = self.clean_condition(
            raw_ad.get("condition", "used")
        )

        image_file = raw_ad.get(
            "image_file"
        )

        return {
            "title": title,
            "description": description,
            "price": price,
            "seller_type": seller_type,
            "testing": testing,
            "warranty": warranty,
            "condition": condition,
            "image_file": image_file
        }

    def collect_many(self, raw_ads):
        collected = []

        if not isinstance(raw_ads, list):
            return collected

        for raw_ad in raw_ads:
            ad = self.collect(raw_ad)

            if ad is not None:
                collected.append(ad)

        return collected

    def clean_text(self, value):
        if value is None:
            return ""

        return " ".join(
            str(value).split()
        )

    def clean_price(self, value):
        if isinstance(value, bool):
            return 0

        try:
            text = (
                str(value)
                .replace(",", "")
                .replace(" ", "")
                .strip()
            )

            if not text:
                return 0

            numbers = re.findall(
                r"\d+",
                text
            )

            if not numbers:
                return 0

            return max(
                0,
                int("".join(numbers))
            )

        except (
            ValueError,
            TypeError
        ):
            return 0

    def clean_bool(self, value):
        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return value != 0

        if isinstance(value, str):
            normalized = (
                value.strip()
                .lower()
            )

            if normalized in (
                "true",
                "1",
                "yes",
                "y",
                "on",
                "بله",
                "بلی"
            ):
                return True

            if normalized in (
                "false",
                "0",
                "no",
                "n",
                "off",
                "خیر",
                "نه"
            ):
                return False

        return False

    def clean_seller_type(
        self,
        seller_type
    ):
        value = str(
            seller_type or ""
        ).strip().lower()

        mapping = {
            "personal": "personal",
            "private": "personal",
            "individual": "personal",
            "شخصی": "personal",
            "business": "business",
            "company": "business",
            "shop": "business",
            "store": "business",
            "فروشگاه": "business",
            "شرکتی": "business"
        }

        return mapping.get(
            value,
            "unknown"
        )

    def clean_condition(
        self,
        condition
    ):
        value = str(
            condition or ""
        ).strip().lower()

        mapping = {
            "used": "used",
            "second hand": "used",
            "دست دوم": "used",
            "کارکرده": "used",
            "new": "new",
            "نو": "new"
        }

        return mapping.get(
            value,
            "unknown"
        )