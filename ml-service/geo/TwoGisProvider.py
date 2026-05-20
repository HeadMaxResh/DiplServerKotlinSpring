import requests


class TwoGisProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def search_nearby(self, lat: float, lon: float, query: str, radius: int = 1500):
        url = "https://catalog.api.2gis.com/3.0/items"

        params = {
            "q": query,
            "point": f"{lon},{lat}",
            "radius": radius,
            "fields": "items.point,items.name,items.address_name",
            "key": self.api_key
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()

        items = data.get("result", {}).get("items", [])

        result = []

        for item in items:
            point = item.get("point")

            if not point:
                continue

            obj_lat = point.get("lat")
            obj_lon = point.get("lon")

            distance = self.distance(lat, lon, obj_lat, obj_lon)

            result.append({
                "name": item.get("name", "Без названия"),
                "address": item.get("address_name"),
                "distanceMeters": round(distance),
                "source": "2gis"
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