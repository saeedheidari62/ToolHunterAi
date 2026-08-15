class AdNormalizer:

    def normalize(self, raw_ad):

        if not isinstance(raw_ad, dict):
            return {
                "valid": False,
                "errors": [
                    "Advertisement data must be an object."
                ]
            }

        errors = []

        title = self._clean_text(
            raw_ad.get("title", "")
        )

        description = self._clean_text(
            raw_ad.get("description", "")
        )

        price = self._normalize_price(
            raw_ad.get("price")
        )

        seller_type = self._normalize_seller_type(
            raw_ad.get("seller_type", "")
        )

        testing = self._normalize_boolean(
            raw_ad.get("testing", False)
        )

        warranty = self._normalize_boolean(
            raw_ad.get("warranty", False)
        )

        condition = self._normalize_condition(
            raw_ad.get("condition", "Used")
        )

        image_file = raw_ad.get(
            "image_file"
        )

        image_urls = raw_ad.get(
            "image_urls",
            []
        )

        if not isinstance(image_urls, list):
            image_urls = []

        if not title:
            errors.append(
                "Title is required."
            )

        if not description:
            errors.append(
                "Description is required."
            )

        if price is None or price <= 0:
            errors.append(
                "A valid price is required."
            )

        if seller_type == "Unknown":
            errors.append(
                "Seller type is required."
            )

        if errors:
            return {
                "valid": False,
                "errors": errors
            }

        return {
            "valid": True,
            "ad": {
                "title": title,
                "description": description,
                "price": price,
                "seller_type": seller_type,
                "testing": testing,
                "warranty": warranty,
                "condition": condition,
                "image_file": image_file,
                "image_urls": image_urls
            }
        }

    def _clean_text(self, value):

        if value is None:
            return ""

        return str(value).strip()

    def _normalize_price(self, value):

        if value is None:
            return None

        if isinstance(value, bool):
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return int(value)

        text = str(value)

        replacements = {
            ",": "",
            "٬": "",
            "تومان": "",
            "ریال": "",
            " ": ""
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        try:
            return int(text)

        except ValueError:
            return None

    def _normalize_seller_type(self, value):

        text = str(value).strip().lower()

        personal_values = [
            "personal",
            "person",
            "individual",
            "شخصی",
            "فردی"
        ]

        business_values = [
            "business",
            "company",
            "shop",
            "dealer",
            "کسب‌وکار",
            "فروشگاه",
            "شرکتی",
            "premium-panel",
        ]

        if text in personal_values:
            return "Personal"

        if text in business_values:
            return "Business"

        return "Unknown"

    def _normalize_boolean(self, value):

        if isinstance(value, bool):
            return value

        text = str(value).strip().lower()

        true_values = [
            "true",
            "yes",
            "y",
            "1",
            "بله",
            "دارد"
        ]

        return text in true_values

    def _normalize_condition(self, value):

        text = str(value).strip().lower()

        new_values = [
            "new",
            "نو"
        ]

        used_values = [
            "used",
            "second hand",
            "دست دوم",
            "کارکرده"
        ]

        if text in new_values:
            return "New"

        if text in used_values:
            return "Used"

        return "Used"