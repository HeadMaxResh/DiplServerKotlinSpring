class PriceEvaluator:

    def evaluate_price(
            self,
            area: float,
            rooms: int,
            text_result: dict,
            image_result: dict,
            geo_result: dict,
            market_result: dict
    ):
        market_base_price = self._get_market_base_price(
            area=area,
            rooms=rooms,
            market_result=market_result
        )

        text_coefficient = text_result.get("priceImpact", {}).get("coefficient", 1.0)

        image_coefficient = image_result.get(
            "apartmentSummary", {}
        ).get(
            "priceImpact", {}
        ).get("coefficient", 1.0)

        geo_coefficient = geo_result.get("priceImpact", {}).get("coefficient", 1.0)

        recommended_price = int(
            market_base_price
            * text_coefficient
            * image_coefficient
            * geo_coefficient
        )

        return {
            "recommendedPrice": recommended_price,
            "minPrice": int(recommended_price * 0.92),
            "maxPrice": int(recommended_price * 1.08),
            "marketBasePrice": int(market_base_price),
            "averagePricePerSquareMeter": (
                market_result or {}
            ).get("averagePricePerSquareMeter"),
            "medianPricePerSquareMeter": (
                market_result or {}
            ).get("medianPricePerSquareMeter"),
            "marketAdsCount": (
                market_result or {}
            ).get("usedAdsCount", 0),
            "coefficients": {
                "textCoefficient": text_coefficient,
                "imageCoefficient": image_coefficient,
                "geoCoefficient": geo_coefficient
            },
            "priceFactors": self._build_price_factors(
                text_coefficient,
                image_coefficient,
                geo_coefficient,
                market_result
            )
        }

    def _get_market_base_price(
            self,
            area: float,
            rooms: int,
            market_result: dict
    ):
        if market_result and market_result.get("success"):
            market_base_price = market_result.get("marketBasePrice")

            if market_base_price and market_base_price > 0:
                return market_base_price

        fallback_price_m2 = {
            1: 1000,
            2: 900,
            3: 850,
            4: 800
        }.get(rooms, 750)

        return int(area * fallback_price_m2)

    def _build_price_factors(
            self,
            text_coefficient,
            image_coefficient,
            geo_coefficient,
            market_result
    ):
        factors = []

        if market_result and market_result.get("success"):
            factors.append(
                f"Рыночная база рассчитана по похожим объявлениям: "
                f"{market_result.get('usedAdsCount', 0)} объектов"
            )
        else:
            factors.append("Рыночная база рассчитана по fallback-модели")

        if text_coefficient > 1:
            factors.append("Описание положительно влияет на стоимость")
        elif text_coefficient < 1:
            factors.append("Описание снижает уверенность в оценке")

        if image_coefficient > 1:
            factors.append("Фотографии показывают хорошее состояние квартиры")
        elif image_coefficient < 1:
            factors.append("Фотографии показывают слабое визуальное состояние")

        if geo_coefficient > 1:
            factors.append("Локация положительно влияет на стоимость")
        elif geo_coefficient < 1:
            factors.append("Локация снижает рекомендуемую стоимость")

        return factors