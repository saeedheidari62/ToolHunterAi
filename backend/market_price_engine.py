class MarketPriceEngine:

    def _filter_outliers(self, prices):
        if len(prices) < 4:
            return prices

        values = sorted(prices)

        q1_index = (len(values) - 1) // 4
        q3_index = (len(values) - 1) * 3 // 4

        q1 = values[q1_index]
        q3 = values[q3_index]

        iqr = q3 - q1

        if iqr <= 0:
            return values

        lower = q1 - (1.5 * iqr)
        upper = q3 + (1.5 * iqr)

        return [
            price
            for price in values
            if lower <= price <= upper
        ]

    def calculate(self, prices):
        valid_prices = []

        for price in prices:
            try:
                value = float(price)

                if value > 0:
                    valid_prices.append(value)

            except (TypeError, ValueError):
                continue

        valid_prices = self._filter_outliers(valid_prices)

        if not valid_prices:
            return {
                "valid": False,
                "sample_count": 0,
                "min_price": None,
                "max_price": None,
                "median_price": None
            }

        valid_prices.sort()

        count = len(valid_prices)

        middle = count // 2

        if count % 2 == 0:
            median = (
                valid_prices[middle - 1]
                + valid_prices[middle]
            ) / 2
        else:
            median = valid_prices[middle]

        return {
            "valid": True,
            "sample_count": count,
            "min_price": valid_prices[0],
            "max_price": valid_prices[-1],
            "median_price": median
        }
