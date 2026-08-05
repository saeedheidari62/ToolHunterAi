class AdCollector:
    """
    Collect and normalize advertisement data
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
            "title": title,
            "description": description,
            "price": int(price),
            "seller_type": seller_type,

            # names expected by analyzer
            "has_test": testing,
            "has_warranty": warranty,

            "condition": condition
        }