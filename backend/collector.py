class AdCollector:
    """
    Collect and normalize advertisement data.
    Supports single and multiple ads.
    """

    def __init__(self):
        pass

    def collect(
        self,
        title,
        description,
        price,
        seller_type,
        testing=False,
        warranty=False,
        condition="used"
    ):
        return {
            "title": self.clean_text(title),
            "description": self.clean_text(description),
            "price": self.clean_price(price),
            "seller_type": self.clean_seller_type(seller_type),
            "has_test": self.clean_bool(testing),
            "has_warranty": self.clean_bool(warranty),
            "condition": self.clean_condition(condition)
        }

    def collect_many(self, ads):
        collected = []

        for ad in ads:
            if not isinstance(ad, dict):
                continue

            if not ad.get("title"):
                continue

            collected.append(
                self.collect(
                    title=ad.get("title"),
                    description=ad.get("description", ""),
                    price=ad.get("price", 0),
                    seller_type=ad.get("seller_type", "unknown"),
                    testing=ad.get("testing", False),
                    warranty=ad.get("warranty", False),
                    condition=ad.get("condition", "used")
                )
            )

        return collected

    def clean_text(self, text):
        if text is None:
            return ""

        return " ".join(str(text).split())

    def clean_price(self, price):
        if isinstance(price, bool):
            return 0

        try:
            cleaned = (
                str(price)
                .replace(",", "")
                .replace(" ", "")
                .strip()
            )

            if not cleaned:
                return 0

            value = int(float(cleaned))

            return max(0, value)

        except (ValueError, TypeError):
            return 0

    def clean_bool(self, value):
        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return value != 0

        if isinstance(value, str):
            normalized = value.strip().lower()

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

    def clean_seller_type(self, seller_type):
        value = str(seller_type or "").strip().lower()

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

        return mapping.get(value, "unknown")

    def clean_condition(self, condition):
        value = str(condition or "").strip().lower()

        mapping = {
            "used": "used",
            "second hand": "used",
            "دست دوم": "used",
            "کارکرده": "used",
            "new": "new",
            "نو": "new"
        }

        return mapping.get(value, "unknown")