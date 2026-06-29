import math
import requests
from geopy.geocoders import Nominatim


class GeoAnalyzer:
    def __init__(self):
        self.geocoder = Nominatim(user_agent="diploma_real_estate_geo_analyzer")
        self.overpass_url = "https://overpass-api.de/api/interpreter"

    def analyze_location(self, address: str):
        coordinates = self.geocode_address(address)

        if coordinates is None:
            return {
                "success": False,
                "message": "Не удалось определить координаты по адресу"
            }

        lat = coordinates["lat"]
        lon = coordinates["lon"]

        infrastructure = self.find_nearest_infrastructure(lat, lon)
        scores = self.calculate_scores(infrastructure)

        location_score = round(
            scores["transportScore"] * 0.30 +
            scores["educationScore"] * 0.20 +
            scores["healthcareScore"] * 0.20 +
            scores["commercialScore"] * 0.15 +
            scores["comfortScore"] * 0.10 +
            scores["trafficScore"] * 0.05,
            2
        )

        return {
            "success": True,
            "address": address,
            "coordinates": {
                "lat": lat,
                "lon": lon
            },
            "nearestInfrastructure": infrastructure,
            "scores": {
                **scores,
                "locationScore": location_score
            },
            "qualityLevel": self.get_location_quality_level(location_score),
            "priceImpact": self.calculate_price_impact(location_score),
            "recommendations": self.build_recommendations(scores, infrastructure)
        }

    def geocode_address(self, address: str):
        try:
            location = self.geocoder.geocode(
                address,
                timeout=10
            )

            if location is None:
                return None

            return {
                "lat": location.latitude,
                "lon": location.longitude
            }

        except Exception as e:
            print("GEOCODING ERROR:", e)
            return None

    def find_nearest_infrastructure(self, lat: float, lon: float):
        radius = 1200

        result = {
            "busStops": [],
            "tramStops": [],
            "metroStations": [],
            "schools": [],
            "kindergartens": [],
            "hospitals": [],
            "clinics": [],
            "shops": [],
            "pharmacies": [],
            "parks": [],
            "parking": []
        }

        query = f"""
        [out:json][timeout:20];
        (
          nwr["highway"="bus_stop"](around:{radius},{lat},{lon});
          nwr["railway"="tram_stop"](around:{radius},{lat},{lon});
          nwr["railway"="subway_entrance"](around:{radius},{lat},{lon});
          nwr["station"="subway"](around:{radius},{lat},{lon});

          nwr["amenity"="school"](around:{radius},{lat},{lon});
          nwr["amenity"="kindergarten"](around:{radius},{lat},{lon});
          nwr["amenity"="hospital"](around:{radius},{lat},{lon});
          nwr["amenity"="clinic"](around:{radius},{lat},{lon});
          nwr["amenity"="doctors"](around:{radius},{lat},{lon});

          nwr["shop"="supermarket"](around:{radius},{lat},{lon});
          nwr["shop"="convenience"](around:{radius},{lat},{lon});
          nwr["amenity"="pharmacy"](around:{radius},{lat},{lon});

          nwr["leisure"="park"](around:{radius},{lat},{lon});
          nwr["amenity"="parking"](around:{radius},{lat},{lon});
        );
        out center tags 80;
        """

        try:
            response = requests.post(
                self.overpass_url,
                data={"data": query},
                headers={"User-Agent": "DiplomaRealEstateAnalyzer/1.0"},
                timeout=25
            )

            if response.status_code != 200:
                print("OVERPASS STATUS:", response.status_code)
                return result

            data = response.json()
            elements = data.get("elements", [])

            for element in elements:
                point = self.extract_point(element)

                if point is None:
                    continue

                tags = element.get("tags", {})

                obj = {
                    "name": self.extract_name(tags),
                    "distanceMeters": round(
                        self.calculate_distance(
                            lat,
                            lon,
                            point["lat"],
                            point["lon"]
                        )
                    ),
                    "type": self.extract_type(tags),
                    "osmType": element.get("type"),
                    "osmId": element.get("id")
                }

                category = self.detect_category(tags)

                if category is not None:
                    result[category].append(obj)

            for key in result.keys():
                result[key] = sorted(
                    self.remove_duplicates(result[key]),
                    key=lambda x: x["distanceMeters"]
                )[:3]

            return result

        except Exception as e:
            print("OVERPASS REQUEST ERROR:", e)
            return result

    def detect_category(self, tags: dict):
        amenity = tags.get("amenity")
        shop = tags.get("shop")
        railway = tags.get("railway")
        highway = tags.get("highway")
        station = tags.get("station")
        leisure = tags.get("leisure")

        if highway == "bus_stop":
            return "busStops"

        if railway == "tram_stop":
            return "tramStops"

        if railway == "subway_entrance" or station == "subway":
            return "metroStations"

        if amenity == "school":
            return "schools"

        if amenity == "kindergarten":
            return "kindergartens"

        if amenity == "hospital":
            return "hospitals"

        if amenity in ["clinic", "doctors"]:
            return "clinics"

        if shop in ["supermarket", "convenience"]:
            return "shops"

        if amenity == "pharmacy":
            return "pharmacies"

        if leisure == "park":
            return "parks"

        if amenity == "parking":
            return "parking"

        return None

    def query_category(self, lat: float, lon: float, radius: int, filters: list[str]):
        query_parts = []

        for filter_expr in filters:
            query_parts.append(f'{filter_expr}(around:{radius},{lat},{lon});')

        query = f"""
        [out:json][timeout:45];
        (
          {" ".join(query_parts)}
        );
        out center tags;
        """

        try:
            response = requests.post(
                self.overpass_url,
                data={"data": query},
                headers={
                    "User-Agent": "DiplomaRealEstateAnalyzer/1.0"
                },
                timeout=60
            )

            if response.status_code != 200:
                print("OVERPASS STATUS:", response.status_code)
                print("OVERPASS TEXT:", response.text[:500])
                return []

            try:
                data = response.json()
            except Exception as e:
                print("OVERPASS JSON ERROR:", e)
                print("OVERPASS RAW:", response.text[:500])
                return []

            elements = data.get("elements", [])
            objects = []

            for element in elements:
                point = self.extract_point(element)

                if point is None:
                    continue

                obj_lat = point["lat"]
                obj_lon = point["lon"]

                distance_meters = self.calculate_distance(
                    lat,
                    lon,
                    obj_lat,
                    obj_lon
                )

                tags = element.get("tags", {})

                objects.append({
                    "name": self.extract_name(tags),
                    "distanceMeters": round(distance_meters),
                    "type": self.extract_type(tags),
                    "osmType": element.get("type"),
                    "osmId": element.get("id")
                })

            objects = self.remove_duplicates(objects)
            objects = sorted(objects, key=lambda x: x["distanceMeters"])

            return objects[:5]

        except Exception as e:
            print("OVERPASS REQUEST ERROR:", e)
            return []

    def extract_point(self, element):
        if "lat" in element and "lon" in element:
            return {
                "lat": element["lat"],
                "lon": element["lon"]
            }

        center = element.get("center")

        if center and "lat" in center and "lon" in center:
            return {
                "lat": center["lat"],
                "lon": center["lon"]
            }

        return None

    def extract_name(self, tags: dict):
        return (
            tags.get("name")
            or tags.get("official_name")
            or tags.get("short_name")
            or "Без названия"
        )

    def extract_type(self, tags: dict):
        for key in [
            "amenity",
            "shop",
            "railway",
            "highway",
            "public_transport",
            "leisure",
            "landuse"
        ]:
            if key in tags:
                return f"{key}={tags[key]}"

        return "unknown"

    def remove_duplicates(self, objects):
        seen = set()
        unique = []

        for obj in objects:
            key = (
                obj["name"],
                obj["distanceMeters"] // 25,
                obj["type"]
            )

            if key not in seen:
                seen.add(key)
                unique.append(obj)

        return unique

    def calculate_scores(self, infrastructure):
        return {
            "transportScore": self.calculate_transport_score(infrastructure),
            "educationScore": self.calculate_education_score(infrastructure),
            "healthcareScore": self.calculate_healthcare_score(infrastructure),
            "commercialScore": self.calculate_commercial_score(infrastructure),
            "comfortScore": self.calculate_comfort_score(infrastructure),
            "trafficScore": self.calculate_traffic_score(infrastructure)
        }

    def calculate_transport_score(self, infrastructure):
        nearest = self.nearest_distance([
            infrastructure["busStops"],
            infrastructure["tramStops"],
            infrastructure["metroStations"]
        ])

        if nearest is None:
            return 20
        if nearest <= 200:
            return 100
        if nearest <= 400:
            return 90
        if nearest <= 700:
            return 75
        if nearest <= 1000:
            return 60
        if nearest <= 1500:
            return 45
        return 30

    def calculate_education_score(self, infrastructure):
        school = self.first_distance(infrastructure["schools"])
        kindergarten = self.first_distance(infrastructure["kindergartens"])

        distances = [d for d in [school, kindergarten] if d is not None]

        if not distances:
            return 25

        avg = sum(distances) / len(distances)

        if avg <= 400:
            return 100
        if avg <= 800:
            return 80
        if avg <= 1200:
            return 65
        if avg <= 1800:
            return 45
        return 30

    def calculate_healthcare_score(self, infrastructure):
        hospital = self.first_distance(infrastructure["hospitals"])
        clinic = self.first_distance(infrastructure["clinics"])
        pharmacy = self.first_distance(infrastructure["pharmacies"])

        distances = [d for d in [hospital, clinic, pharmacy] if d is not None]

        if not distances:
            return 30

        avg = sum(distances) / len(distances)

        if avg <= 500:
            return 100
        if avg <= 1000:
            return 80
        if avg <= 1500:
            return 60
        if avg <= 2200:
            return 45
        return 30

    def calculate_commercial_score(self, infrastructure):
        shop = self.first_distance(infrastructure["shops"])

        if shop is None:
            return 35

        if shop <= 250:
            return 100
        if shop <= 500:
            return 85
        if shop <= 900:
            return 70
        if shop <= 1500:
            return 50
        return 35

    def calculate_comfort_score(self, infrastructure):
        park = self.first_distance(infrastructure["parks"])
        parking = self.first_distance(infrastructure["parking"])

        score = 40

        if park is not None:
            if park <= 400:
                score += 45
            elif park <= 800:
                score += 35
            elif park <= 1500:
                score += 20
            else:
                score += 10

        if parking is not None:
            if parking <= 300:
                score += 15
            elif parking <= 700:
                score += 10
            else:
                score += 5

        return min(score, 100)

    def calculate_traffic_score(self, infrastructure):
        transport_objects_count = (
            len(infrastructure["busStops"]) +
            len(infrastructure["tramStops"]) +
            len(infrastructure["metroStations"])
        )

        parking_objects_count = len(infrastructure["parking"])

        score = 75

        if transport_objects_count >= 10:
            score -= 20
        elif transport_objects_count >= 6:
            score -= 10

        if parking_objects_count >= 2:
            score += 10

        return max(30, min(score, 100))

    def first_distance(self, objects):
        if not objects:
            return None

        return objects[0]["distanceMeters"]

    def nearest_distance(self, groups):
        distances = []

        for group in groups:
            if group:
                distances.append(group[0]["distanceMeters"])

        if not distances:
            return None

        return min(distances)

    def get_location_quality_level(self, score):
        if score >= 85:
            return "Отличная локация"
        if score >= 70:
            return "Хорошая локация"
        if score >= 55:
            return "Средняя локация"
        if score >= 40:
            return "Слабая локация"
        return "Плохая локация"

    def calculate_price_impact(self, score):
        if score >= 85:
            return {
                "impact": "strong_positive",
                "coefficient": 1.18,
                "description": "Отличная локация может повысить рекомендуемую стоимость аренды до 18%"
            }

        if score >= 70:
            return {
                "impact": "positive",
                "coefficient": 1.10,
                "description": "Хорошая локация может повысить рекомендуемую стоимость аренды до 10%"
            }

        if score >= 55:
            return {
                "impact": "neutral",
                "coefficient": 1.00,
                "description": "Средняя локация не оказывает существенного влияния на стоимость"
            }

        if score >= 40:
            return {
                "impact": "negative",
                "coefficient": 0.92,
                "description": "Слабая инфраструктура может снизить рекомендуемую стоимость аренды до 8%"
            }

        return {
            "impact": "strong_negative",
            "coefficient": 0.85,
            "description": "Плохая инфраструктурная доступность может снизить рекомендуемую стоимость аренды до 15%"
        }

    def build_recommendations(self, scores, infrastructure):
        recommendations = []

        if scores["transportScore"] < 60:
            recommendations.append("Транспортная доступность ниже среднего: ближайшие остановки находятся далеко.")

        if scores["educationScore"] < 60:
            recommendations.append("Школы и детские сады находятся не в пешей доступности или отсутствуют в открытых данных.")

        if scores["healthcareScore"] < 60:
            recommendations.append("Медицинская инфраструктура расположена недостаточно близко.")

        if scores["commercialScore"] < 60:
            recommendations.append("Магазины и торговые объекты находятся не в ближайшей доступности.")

        if scores["comfortScore"] < 60:
            recommendations.append("Недостаточно парков, зеленых зон или парковочной инфраструктуры рядом.")

        if not recommendations:
            recommendations.append("Локация обладает развитой инфраструктурой и положительно влияет на стоимость аренды.")

        return recommendations

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        radius = 6371000

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)

        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2) ** 2 +
            math.cos(phi1) *
            math.cos(phi2) *
            math.sin(delta_lambda / 2) ** 2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )

        return radius * c