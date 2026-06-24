import os
import re
import math
import time
import requests
from statistics import median
from typing import Optional


class MarketAnalyzer:
    def __init__(self):
        self.base_url = "https://www.ads-api.ru/main/api"
        self.user = os.getenv("ADS_API_USER")
        self.token = os.getenv("ADS_API_TOKEN")
        self.last_request_time = 0

    def analyze_market(self, lat: float, lon: float, city: str, rooms: int, area: float):
        nearby_ads_raw = self._load_ads(
            city=city,
            rooms=rooms,
            lat=lat,
            lon=lon,
            radius_m=1200,
            limit=1000
        )

        nearby_ads = self._prepare_ads(
            ads=nearby_ads_raw,
            target_lat=lat,
            target_lon=lon
        )

        if len(nearby_ads) >= 3:
            return self._build_market_result(
                area=area,
                all_ads_count=len(nearby_ads_raw),
                prepared_ads=nearby_ads,
                quality_source="nearby",
                recommendation="Рыночная цена рассчитана на основе похожих объявлений рядом"
            )

        city_ads_raw = self._load_ads(
            city=city,
            rooms=rooms,
            lat=None,
            lon=None,
            radius_m=None,
            limit=100
        )

        city_ads = self._prepare_ads(
            ads=city_ads_raw,
            target_lat=lat,
            target_lon=lon
        )

        if len(city_ads) >= 3:
            return self._build_market_result(
                area=area,
                all_ads_count=len(city_ads_raw),
                prepared_ads=city_ads,
                quality_source="city",
                recommendation="Рядом недостаточно объявлений, поэтому использована средняя рыночная цена по городу"
            )

        return {
            "success": True,
            "source": "ads-api.ru",
            "marketBasePrice": int(area * 900),
            "averagePricePerSquareMeter": 900,
            "medianPricePerSquareMeter": 900,
            "adsCount": len(nearby_ads_raw),
            "usedAdsCount": len(nearby_ads),
            "cityAdsCount": len(city_ads_raw),
            "usedCityAdsCount": len(city_ads),
            "nearbyAds": nearby_ads[:10],
            "cityAds": city_ads[:10],
            "qualityLevel": "not_enough_market_data",
            "marketSource": "fallback",
            "recommendation": "Недостаточно объявлений рядом и по городу, использована базовая fallback-оценка"
        }

    def _load_ads(
            self,
            city: str,
            rooms: int,
            lat: Optional[float],
            lon: Optional[float],
            radius_m: Optional[int],
            limit: int
    ):
        params = {
            "user": self.user,
            "token": self.token,
            "format": "json",
            "category_id": "2",
            "nedvigimost_type": "2",
            "city": city,
            "withcoords": "1",
            "withphone": "0",
            "is_actual": "11,1",
            "limit": str(limit),
            "sort": "desc",
            "param[2019]": str(rooms),
            "param[2016]": "На длительный срок"
        }

        if lat is not None and lon is not None and radius_m is not None:
            polygon = self._build_area_polygon(lat, lon, radius_m)

            for i, point in enumerate(polygon):
                params[f"area[{i}][lat]"] = point["lat"]
                params[f"area[{i}][lng]"] = point["lng"]

        self._respect_rate_limit()

        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=30
            )

            data = response.json()

            if data.get("code") != 200:
                print("ADS API ERROR:", data)
                return []

            return data.get("data", [])

        except Exception as e:
            print("ADS API REQUEST ERROR:", e)
            return []

    def _build_market_result(
            self,
            area: float,
            all_ads_count: int,
            prepared_ads: list,
            quality_source: str,
            recommendation: str
    ):
        prices_per_meter = [
            ad["pricePerSquareMeter"]
            for ad in prepared_ads
            if ad["pricePerSquareMeter"] > 0
        ]

        median_price_m2 = median(prices_per_meter)
        avg_price_m2 = sum(prices_per_meter) / len(prices_per_meter)
        market_base_price = int(median_price_m2 * area)

        return {
            "success": True,
            "source": "ads-api.ru",
            "marketBasePrice": market_base_price,
            "averagePricePerSquareMeter": round(avg_price_m2, 2),
            "medianPricePerSquareMeter": round(median_price_m2, 2),
            "adsCount": all_ads_count,
            "usedAdsCount": len(prepared_ads),
            "nearbyAds": prepared_ads[:10],
            "qualityLevel": self._quality_level(len(prepared_ads)),
            "marketSource": quality_source,
            "recommendation": recommendation
        }

    def _prepare_ads(self, ads, target_lat, target_lon):
        result = []

        for ad in ads:
            if not self._is_long_term_rent(ad):
                continue

            price = self._safe_float(ad.get("price"))
            ad_area = self._extract_area(ad)

            if price <= 0:
                continue

            if ad_area <= 0:
                continue

            coords = ad.get("coords") or {}
            ad_lat = self._safe_float(coords.get("lat"))
            ad_lon = self._safe_float(coords.get("lng"))

            distance = None
            if target_lat is not None and target_lon is not None and ad_lat and ad_lon:
                distance = self._distance_meters(
                    target_lat,
                    target_lon,
                    ad_lat,
                    ad_lon
                )

            price_m2 = price / ad_area

            if price_m2 < 100 or price_m2 > 10000:
                continue

            result.append({
                "id": ad.get("id"),
                "title": ad.get("title"),
                "price": int(price),
                "area": ad_area,
                "pricePerSquareMeter": round(price_m2, 2),
                "address": ad.get("address"),
                "city": ad.get("city1") or ad.get("city"),
                "source": ad.get("source"),
                "url": ad.get("url"),
                "distanceMeters": int(distance) if distance is not None else None
            })

        result.sort(
            key=lambda x: x["distanceMeters"]
            if x["distanceMeters"] is not None
            else 999999
        )

        return result

    def _is_long_term_rent(self, ad):
        rent_period = str(ad.get("param_2016", "")).lower()

        params = ad.get("params") or {}
        params_period = str(params.get("Срок аренды", "")).lower()

        price_metric = str(ad.get("price_metric", "")).lower()

        if "посуточно" in rent_period:
            return False

        if "посуточно" in params_period:
            return False

        if "сутки" in price_metric:
            return False

        if "длительный" in rent_period:
            return True

        if "длительный" in params_period:
            return True

        if "месяц" in price_metric:
            return True

        return False

    def _extract_area(self, ad):
        possible_keys = [
            "area",
            "square",
            "square_meter",
            "meters",
            "total_area",
            "living_area",
            "param_2313",
            "param_2515",
            "param_2463",
            "param_2017",
            "param_2009"
        ]

        for key in possible_keys:
            area = self._safe_float(ad.get(key))
            if area > 0:
                return area

        params = ad.get("params") or {}

        if isinstance(params, dict):
            for key, value in params.items():
                key_lower = str(key).lower()
                value_str = str(value).lower()

                if (
                        "площад" in key_lower
                        or "area" in key_lower
                        or "метраж" in key_lower
                ):
                    area = self._safe_float(value)
                    if area > 0:
                        return area

                if "площад" in value_str:
                    area = self._safe_float(value)
                    if area > 0:
                        return area

        for key, value in ad.items():
            key_lower = str(key).lower()

            if (
                    "площад" in key_lower
                    or "area" in key_lower
                    or "square" in key_lower
            ):
                area = self._safe_float(value)
                if area > 0:
                    return area

        return 0

    def _build_area_polygon(self, lat, lon, radius_m):
        lat_delta = radius_m / 111_320
        lon_delta = radius_m / (
                111_320 * math.cos(math.radians(lat))
        )

        return [
            {"lat": lat - lat_delta, "lng": lon - lon_delta},
            {"lat": lat - lat_delta, "lng": lon + lon_delta},
            {"lat": lat + lat_delta, "lng": lon + lon_delta},
            {"lat": lat + lat_delta, "lng": lon - lon_delta}
        ]

    def _respect_rate_limit(self):
        elapsed = time.time() - self.last_request_time

        if elapsed < 5:
            time.sleep(5 - elapsed)

        self.last_request_time = time.time()

    def _distance_meters(self, lat1, lon1, lat2, lon2):
        r = 6371000

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)

        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lon2 - lon1)

        a = (
                math.sin(d_phi / 2) ** 2
                + math.cos(phi1)
                * math.cos(phi2)
                * math.sin(d_lambda / 2) ** 2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )

        return r * c

    def _safe_float(self, value):
        try:
            if value is None:
                return 0

            if isinstance(value, (int, float)):
                return float(value)

            text = str(value)
            text = text.replace(",", ".")
            text = text.replace("\xa0", " ")

            match = re.search(r"\d+(\.\d+)?", text)

            if not match:
                return 0

            return float(match.group(0))

        except Exception:
            return 0

    def _quality_level(self, count):
        if count >= 20:
            return "high_market_confidence"
        if count >= 10:
            return "medium_market_confidence"
        if count >= 3:
            return "low_market_confidence"

        return "not_enough_market_data"