import re


class TextAnalyzer:
    def analyze_text(self, description: str):
        normalized_text = self.normalize_text(description)

        if not normalized_text or len(normalized_text) < 20:
            return {
                "success": False,
                "message": "Описание слишком короткое для анализа"
            }

        apartment_features = self.extract_apartment_features(normalized_text)
        repair_features = self.extract_repair_features(normalized_text)
        furniture_features = self.extract_furniture_features(normalized_text)
        appliances_features = self.extract_appliances_features(normalized_text)
        tenant_rules = self.extract_tenant_rules(normalized_text)
        quality_score = self.calculate_description_quality_score(normalized_text)

        text_score = self.calculate_text_score(
            apartment_features,
            repair_features,
            furniture_features,
            appliances_features,
            quality_score
        )

        return {
            "success": True,
            "textLength": len(description),
            "normalizedTextLength": len(normalized_text),
            "apartmentFeatures": apartment_features,
            "repairFeatures": repair_features,
            "furnitureFeatures": furniture_features,
            "appliancesFeatures": appliances_features,
            "tenantRules": tenant_rules,
            "scores": {
                "descriptionQualityScore": quality_score,
                "textFeatureScore": text_score
            },
            "qualityLevel": self.get_quality_level(text_score),
            "priceImpact": self.calculate_price_impact(text_score),
            "recommendations": self.build_recommendations(
                apartment_features,
                repair_features,
                furniture_features,
                appliances_features,
                tenant_rules,
                quality_score
            )
        }

    def normalize_text(self, text: str):
        text = text.lower()
        text = text.replace("ё", "е")
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text

    def extract_apartment_features(self, text: str):
        rooms = self.extract_rooms(text)
        area = self.extract_area(text)
        floor = self.extract_floor(text)

        return {
            "rooms": rooms,
            "area": area,
            "floor": floor,
            "hasBalcony": self.contains_any(text, [
                "балкон", "лоджия"
            ]),
            "hasParking": self.contains_any(text, [
                "парковка", "паркинг", "машиноместо"
            ]),
            "hasElevator": self.contains_any(text, [
                "лифт", "грузовой лифт", "пассажирский лифт"
            ]),
            "isStudio": self.contains_any(text, [
                "студия", "квартира-студия"
            ]),
            "hasSeparateRooms": self.contains_any(text, [
                "изолированные комнаты", "раздельные комнаты"
            ])
        }

    def extract_rooms(self, text: str):
        patterns = [
            r"(\d+)\s*[- ]?комнат",
            r"(\d+)\s*к\b",
            r"(\d+)\s*комн",
            r"однокомнат",
            r"двухкомнат",
            r"трехкомнат",
            r"трёхкомнат",
            r"четырехкомнат"
        ]

        word_rooms = {
            "однокомнат": 1,
            "двухкомнат": 2,
            "трехкомнат": 3,
            "трёхкомнат": 3,
            "четырехкомнат": 4
        }

        for word, value in word_rooms.items():
            if word in text:
                return value

        for pattern in patterns[:3]:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

        if "студия" in text:
            return 1

        return None

    def extract_area(self, text: str):
        patterns = [
            r"(\d+(?:[.,]\d+)?)\s*м2",
            r"(\d+(?:[.,]\d+)?)\s*м²",
            r"площад[ьиь]?\s*(\d+(?:[.,]\d+)?)",
            r"(\d+(?:[.,]\d+)?)\s*кв\.?\s*м"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1).replace(",", "."))

        return None

    def extract_floor(self, text: str):
        patterns = [
            r"(\d+)\s*/\s*(\d+)\s*этаж",
            r"(\d+)\s*этаж",
            r"этаж\s*(\d+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 2:
                    return {
                        "floor": int(match.group(1)),
                        "totalFloors": int(match.group(2))
                    }

                return {
                    "floor": int(match.group(1)),
                    "totalFloors": None
                }

        return None

    def extract_repair_features(self, text: str):
        repair_quality = "unknown"

        if self.contains_any(text, [
            "евроремонт",
            "дизайнерский ремонт",
            "премиальный ремонт",
            "новый ремонт",
            "современный ремонт",
            "свежий ремонт",
            "качественный ремонт"
        ]):
            repair_quality = "good"

        if self.contains_any(text, [
            "косметический ремонт",
            "обычный ремонт",
            "жилое состояние",
            "чистая квартира"
        ]):
            repair_quality = "basic"

        if self.contains_any(text, [
            "без ремонта",
            "требуется ремонт",
            "старый ремонт",
            "убитая",
            "плохое состояние",
            "нужен ремонт"
        ]):
            repair_quality = "poor"

        if self.contains_any(text, [
            "премиум",
            "люкс",
            "бизнес-класс",
            "элитный ремонт"
        ]):
            repair_quality = "premium"

        return {
            "repairQuality": repair_quality,
            "hasNewRepair": self.contains_any(text, [
                "новый ремонт", "свежий ремонт", "после ремонта"
            ]),
            "hasDesignRepair": self.contains_any(text, [
                "дизайнерский ремонт", "дизайн-проект"
            ]),
            "needsRepair": self.contains_any(text, [
                "требуется ремонт", "нужен ремонт", "без ремонта"
            ])
        }

    def extract_furniture_features(self, text: str):
        has_furniture = self.contains_any(text, [
            "мебель", "меблированная", "меблирована", "с мебелью"
        ])

        no_furniture = self.contains_any(text, [
            "без мебели", "пустая квартира"
        ])

        furniture_condition = "unknown"

        if self.contains_any(text, [
            "новая мебель", "современная мебель", "качественная мебель"
        ]):
            furniture_condition = "good"

        if self.contains_any(text, [
            "старая мебель", "изношенная мебель"
        ]):
            furniture_condition = "poor"

        if has_furniture and furniture_condition == "unknown":
            furniture_condition = "basic"

        if no_furniture:
            furniture_condition = "none"

        return {
            "hasFurniture": has_furniture and not no_furniture,
            "noFurniture": no_furniture,
            "furnitureCondition": furniture_condition,
            "hasKitchenFurniture": self.contains_any(text, [
                "кухонный гарнитур", "кухня", "встроенная кухня"
            ]),
            "hasWardrobe": self.contains_any(text, [
                "шкаф", "гардероб", "шкаф-купе"
            ]),
            "hasBed": self.contains_any(text, [
                "кровать", "спальное место"
            ]),
            "hasSofa": self.contains_any(text, [
                "диван"
            ])
        }

    def extract_appliances_features(self, text: str):
        appliances = {
            "refrigerator": self.contains_any(text, [
                "холодильник"
            ]),
            "washingMachine": self.contains_any(text, [
                "стиральная машина", "стиралка"
            ]),
            "dishwasher": self.contains_any(text, [
                "посудомоечная машина", "посудомойка"
            ]),
            "airConditioner": self.contains_any(text, [
                "кондиционер", "сплит-система"
            ]),
            "tv": self.contains_any(text, [
                "телевизор", "тв"
            ]),
            "microwave": self.contains_any(text, [
                "микроволновка", "свч"
            ]),
            "internet": self.contains_any(text, [
                "интернет", "wi-fi", "wifi", "вайфай"
            ])
        }

        count = sum(1 for value in appliances.values() if value)

        return {
            **appliances,
            "appliancesCount": count,
            "appliancesLevel": self.get_appliances_level(count)
        }

    def extract_tenant_rules(self, text: str):
        return {
            "petsAllowed": self.contains_any(text, [
                "можно с животными", "с животными можно", "разрешены животные"
            ]),
            "petsForbidden": self.contains_any(text, [
                "без животных", "животные запрещены", "с животными нельзя"
            ]),
            "childrenAllowed": self.contains_any(text, [
                "можно с детьми", "с детьми можно"
            ]),
            "childrenForbidden": self.contains_any(text, [
                "без детей", "с детьми нельзя"
            ]),
            "smokingForbidden": self.contains_any(text, [
                "не курить", "курение запрещено", "без курения"
            ]),
            "longTermOnly": self.contains_any(text, [
                "на длительный срок", "долгосрочно", "длительная аренда"
            ]),
            "depositMentioned": self.contains_any(text, [
                "залог", "депозит"
            ]),
            "utilitiesMentioned": self.contains_any(text, [
                "коммунальные", "ку", "счетчики", "свет и вода"
            ])
        }

    def calculate_description_quality_score(self, text: str):
        score = 0

        length = len(text)

        if length >= 500:
            score += 35
        elif length >= 250:
            score += 25
        elif length >= 100:
            score += 15
        else:
            score += 5

        important_keywords = [
            "ремонт",
            "мебель",
            "техника",
            "интернет",
            "балкон",
            "залог",
            "коммунальные",
            "метро",
            "остановка",
            "магазин",
            "школа",
            "детский сад"
        ]

        keyword_count = sum(1 for word in important_keywords if word in text)
        score += min(keyword_count * 5, 40)

        if re.search(r"\d+\s*м", text):
            score += 10

        if re.search(r"\d+\s*/\s*\d+", text):
            score += 5

        if self.contains_any(text, ["залог", "депозит", "коммунальные"]):
            score += 10

        return min(score, 100)

    def calculate_text_score(
            self,
            apartment_features,
            repair_features,
            furniture_features,
            appliances_features,
            quality_score
    ):
        score = 0

        score += quality_score * 0.25

        repair_scores = {
            "poor": 20,
            "basic": 50,
            "good": 80,
            "premium": 100,
            "unknown": 45
        }

        furniture_scores = {
            "none": 25,
            "poor": 35,
            "basic": 60,
            "good": 85,
            "unknown": 45
        }

        appliances_scores = {
            "none": 20,
            "low": 40,
            "medium": 70,
            "high": 90
        }

        score += repair_scores.get(
            repair_features["repairQuality"],
            45
        ) * 0.30

        score += furniture_scores.get(
            furniture_features["furnitureCondition"],
            45
        ) * 0.20

        score += appliances_scores.get(
            appliances_features["appliancesLevel"],
            40
        ) * 0.15

        if apartment_features["hasBalcony"]:
            score += 5

        if apartment_features["hasParking"]:
            score += 5

        return round(min(score, 100), 2)

    def get_appliances_level(self, count: int):
        if count == 0:
            return "none"
        if count <= 2:
            return "low"
        if count <= 5:
            return "medium"
        return "high"

    def get_quality_level(self, score: float):
        if score >= 85:
            return "Отличное описание"
        if score >= 70:
            return "Хорошее описание"
        if score >= 50:
            return "Среднее описание"
        if score >= 30:
            return "Слабое описание"
        return "Плохое описание"

    def calculate_price_impact(self, score: float):
        if score >= 85:
            return {
                "impact": "strong_positive",
                "coefficient": 1.12,
                "description": "Описание содержит признаки высокого качества жилья и может повысить оценку аренды до 12%"
            }

        if score >= 70:
            return {
                "impact": "positive",
                "coefficient": 1.07,
                "description": "Описание содержит положительные признаки и может повысить оценку аренды до 7%"
            }

        if score >= 50:
            return {
                "impact": "neutral",
                "coefficient": 1.00,
                "description": "Описание не оказывает существенного влияния на стоимость"
            }

        if score >= 30:
            return {
                "impact": "negative",
                "coefficient": 0.95,
                "description": "Описание неполное, возможна пониженная точность оценки"
            }

        return {
            "impact": "strong_negative",
            "coefficient": 0.90,
            "description": "Описание недостаточно информативно и может снизить доверие к объявлению"
        }

    def build_recommendations(
            self,
            apartment_features,
            repair_features,
            furniture_features,
            appliances_features,
            tenant_rules,
            quality_score
    ):
        recommendations = []

        if apartment_features["rooms"] is None:
            recommendations.append("Рекомендуется указать количество комнат.")

        if apartment_features["area"] is None:
            recommendations.append("Рекомендуется указать площадь квартиры.")

        if repair_features["repairQuality"] == "unknown":
            recommendations.append("Рекомендуется подробнее описать состояние ремонта.")

        if furniture_features["furnitureCondition"] == "unknown":
            recommendations.append("Рекомендуется указать наличие и состояние мебели.")

        if appliances_features["appliancesCount"] == 0:
            recommendations.append("Рекомендуется указать наличие бытовой техники.")

        if not tenant_rules["depositMentioned"]:
            recommendations.append("Рекомендуется указать условия залога или депозита.")

        if not tenant_rules["utilitiesMentioned"]:
            recommendations.append("Рекомендуется указать порядок оплаты коммунальных услуг.")

        if quality_score < 50:
            recommendations.append("Описание слишком короткое или недостаточно информативное.")

        if not recommendations:
            recommendations.append("Описание достаточно информативное и подходит для оценки стоимости.")

        return recommendations

    def contains_any(self, text: str, words: list[str]):
        return any(word in text for word in words)