class AdCollector:
    """
    Collect and normalize advertisement data
    Supports single and multiple ads
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
        condition="Used"
    ):

        return {
            "title": self.clean_text(title),
            "description": self.clean_text(description),
            "price": self.clean_price(price),
            "seller_type": seller_type.lower(),

            "has_test": bool(testing),
            "has_warranty": bool(warranty),

            "condition": condition.lower()
        }


    def collect_many(self, ads):

        collected = []

        for ad in ads:

            if not ad.get("title"):
                continue

            collected.append(
                self.collect(
                    title=ad.get("title"),
                    description=ad.get("description", ""),
                    price=ad.get("price", 0),
                    seller_type=ad.get(
                        "seller_type",
                        "unknown"
                    ),
                    testing=ad.get(
                        "testing",
                        False
                    ),
                    warranty=ad.get(
                        "warranty",
                        False
                    ),
                    condition=ad.get(
                        "condition",
                        "used"
                    )
                )
            )

        return collected


    def clean_text(self, text):

        if not text:
            return ""

        return " ".join(
            str(text).split()
        )


    def clean_price(self, price):

        try:
            return int(
                str(price)
                .replace(",", "")
                .replace(" ", "")
            )

        except:

            return 0