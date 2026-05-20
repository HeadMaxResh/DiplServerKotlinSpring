class PriceEvaluator:

    def evaluate_price(
            self,
            area: float,
            rooms: int,
            text_result: dict,
            image_result: dict,
            geo_result: dict
    ):
        market_base_price = self.calculate_market_base_price(
            area=area,
            rooms=rooms,
            geo_result=geo_result
        )

        text_coefficient = self.extract_coefficient(text_result, 1.00)
        image_coefficient = self.extract_image_coefficient(image_result)
        geo_coefficient = self.extract_geo_coefficient(geo_result)

        final_price = (
                market_base_price *
                text_coefficient *
                image_coefficient *
                geo_coefficient
        )

        final_price = round(final_price / 100) * 100

        return {
            "marketBasePrice": int(market_base_price),
            "finalRecommendedPrice": int(final_price),
            "minPrice": int(final_price * 0.92),
            "maxPrice": int(final_price * 1.08),
            "coefficients": {
                "textCoefficient": text_coefficient,
                "imageCoefficient": image_coefficient,
                "geoCoefficient": geo_coefficient
            },
            "priceFactors": self.build_price_factors(
                text_result,
                image_result,
                geo_result,
                text_coefficient,
                image_coefficient,
                geo_coefficient
            )
        }

    def calculate_market_base_price(self, area: float, rooms: int, geo_result: dict):
        """
        Базовая рыночная цена.
        Пока используется экспертная модель.
        Позже сюда можно подключить ML-модель или реальные объявления района.
        """

        city = self.extract_city(geo_result)

        price_per_meter = {
            "москва": 1800,
            "санкт-петербург": 1400,
            "саратов": 650,
            "казань": 1000,
            "екатеринбург": 950,
            "новосибирск": 850
        }

        base_meter_price = price_per_meter.get(city, 750)

        base_price = area * base_meter_price

        room_coefficient = {
            1: 1.00,
            2: 1.12,
            3: 1.22,
            4: 1.30
        }.get(rooms, 1.00)

        return base_price * room_coefficient

    def extract_city(self, geo_result: dict):
        address = geo_result.get("address", "").lower()

        known_cities = [
            "москва",
            "санкт-петербург",
            "саратов",
            "казань",
            "екатеринбург",
            "новосибирск"
        ]

        for city in known_cities:
            if city in address:
                return city

        return "unknown"

    def extract_coefficient(self, result: dict, default: float):
        try:
            return result["priceImpact"]["coefficient"]
        except Exception:
            return default

    def extract_geo_coefficient(self, geo_result: dict):
        return self.extract_coefficient(geo_result, 1.00)

    def extract_image_coefficient(self, image_result: dict):
        try:
            return image_result["apartmentSummary"]["priceImpact"]["coefficient"]
        except Exception:
            return 1.00

    def build_price_factors(
            self,
            text_result,
            image_result,
            geo_result,
            text_coefficient,
            image_coefficient,
            geo_coefficient
    ):
        factors = []

        if text_coefficient > 1:
            factors.append("Текстовое описание содержит положительные характеристики квартиры")
        elif text_coefficient < 1:
            factors.append("Текстовое описание недостаточно информативно или содержит понижающие признаки")

        if image_coefficient > 1:
            factors.append("Фотографии показывают хорошее визуальное состояние квартиры")
        elif image_coefficient < 1:
            factors.append("По фотографиям выявлены признаки сниженного качества жилья")

        if geo_coefficient > 1:
            factors.append("Локация и инфраструктура положительно влияют на стоимость")
        elif geo_coefficient < 1:
            factors.append("Инфраструктурная доступность снижает оценку стоимости")

        return factors