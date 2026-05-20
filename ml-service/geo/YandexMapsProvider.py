import requests


class YandexMapsProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def geocode(self, address: str):
        url = "https://geocode-maps.yandex.ru/1.x/"

        params = {
            "apikey": self.api_key,
            "geocode": address,
            "format": "json"
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()

        members = data["response"]["GeoObjectCollection"]["featureMember"]

        if not members:
            return None

        pos = members[0]["GeoObject"]["Point"]["pos"]
        lon, lat = map(float, pos.split())

        return {
            "lat": lat,
            "lon": lon
        }

    def search_nearby(self, lat: float, lon: float, text: str, radius: int = 1500):
        url = "https://search-maps.yandex.ru/v1/"

        params = {
            "apikey": self.api_key,
            "text": text,
            "lang": "ru_RU",
            "ll": f"{lon},{lat}",
            "spn": "0.03,0.03",
            "type": "biz",
            "results": 10
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()

        result = []

        for feature in data.get("features", []):
            geometry = feature.get("geometry", {})
            properties = feature.get("properties", {})

            coords = geometry.get("coordinates")

            if not coords:
                continue

            obj_lon, obj_lat = coords

            distance = self.distance(lat, lon, obj_lat, obj_lon)

            if distance <= radius:
                result.append({
                    "name": properties.get("name", "Без названия"),
                    "distanceMeters": round(distance),
                    "source": "yandex"
                })

        return sorted(result, key=lambda x: x["distanceMeters"])

    def distance(self, lat1, lon1, lat2, lon2):
        import math

        r = 6371000

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)

        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = (
            math.sin(dphi / 2) ** 2
            + math.cos(phi1)
            * math.cos(phi2)
            * math.sin(dlambda / 2) ** 2
        )

        return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))