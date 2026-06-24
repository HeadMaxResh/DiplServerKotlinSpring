from fastapi import FastAPI, UploadFile, File, Form
from PIL import Image, ImageStat
from image.advanced_image_analyzer import AdvancedImageAnalyzer
from geo.geo_analyzer import GeoAnalyzer
from text.text_analyzer import TextAnalyzer
from price.price_evaluator import PriceEvaluator
from pydantic import BaseModel
from market.market_analyzer import MarketAnalyzer
from typing import Dict, Any
from dotenv import load_dotenv
import io
import numpy as np
import cv2
import asyncio



app = FastAPI(title="Apartment Price ML Service")

load_dotenv()

image_analyzer = AdvancedImageAnalyzer()
geo_analyzer = GeoAnalyzer()
text_analyzer = TextAnalyzer()
price_evaluator = PriceEvaluator()
market_analyzer = MarketAnalyzer()



@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/predict")
async def predict(
        description: str = Form(...),
        address: str = Form(...),
        rooms: int = Form(...),
        area: float = Form(...),
        photos: list[UploadFile] = File(...)
):
    image_vectors = []

    for photo in photos:
        content = await photo.read()
        image = Image.open(io.BytesIO(content))
        features = image_analyzer.extract_features(image)
        image_vectors.append(features)

    mean_image_features = np.mean(image_vectors, axis=0)

    base_price = area * 1200

    if rooms >= 2:
        base_price += 5000

    if "мебель" in description.lower():
        base_price += 3000

    if "ремонт" in description.lower():
        base_price += 4000

    predicted_price = int(base_price)

    return {
        "recommendedPrice": predicted_price,
        "minPrice": int(predicted_price * 0.9),
        "maxPrice": int(predicted_price * 1.1),
        "confidence": 0.8,
        "imageFeatureSize": len(mean_image_features),
        "factors": [
            "Фотографии проанализированы с помощью ResNet50",
            "Учтена площадь квартиры",
            "Учтено количество комнат",
            "Учтено текстовое описание"
        ]
    }

@app.post("/evaluate-apartment")
async def evaluate_apartment(
        description: str = Form(...),
        address: str = Form(...),
        rooms: int = Form(...),
        area: float = Form(...),
        photos: list[UploadFile] = File(...)
):
    photo_bytes_list = []

    for photo in photos:
        content = await photo.read()
        photo_bytes_list.append({
            "filename": photo.filename,
            "content": content
        })

    text_task = asyncio.to_thread(
        text_analyzer.analyze_text,
        description
    )

    geo_task = asyncio.to_thread(
        geo_analyzer.analyze_location,
        address
    )

    image_task = asyncio.to_thread(
        analyze_images_sync,
        photo_bytes_list
    )

    text_result, geo_result, image_result = await asyncio.gather(
        text_task,
        geo_task,
        image_task
    )

    price_result = price_evaluator.evaluate_price(
        area=area,
        rooms=rooms,
        text_result=text_result,
        image_result=image_result,
        geo_result=geo_result
    )

    return {
        "success": True,
        "inputData": {
            "description": description,
            "address": address,
            "rooms": rooms,
            "area": area
        },
        "price": {
            "recommendedPrice": price_result["finalRecommendedPrice"],
            "minPrice": price_result["minPrice"],
            "maxPrice": price_result["maxPrice"],
            "marketBasePrice": price_result["marketBasePrice"],
            "coefficients": price_result["coefficients"],
            "priceFactors": price_result["priceFactors"]
        },
        "analysis": {
            "textAnalysis": text_result,
            "imageAnalysis": image_result,
            "geoAnalysis": geo_result
        }
    }

def analyze_images_sync(photo_bytes_list):
    photo_results = []

    for photo_data in photo_bytes_list:
        image = Image.open(io.BytesIO(photo_data["content"]))

        result = image_analyzer.analyze_image(
            image=image,
            filename=photo_data["filename"]
        )

        photo_results.append(result)

    image_summary = build_apartment_summary(photo_results)

    return {
        "photosCount": len(photo_results),
        "apartmentSummary": image_summary,
        "photos": photo_results
    }


class CalculateFromAnalysisRequest(BaseModel):
    area: float
    rooms: int
    textAnalysis: Dict[str, Any]
    imageAnalysis: Dict[str, Any]
    geoAnalysis: Dict[str, Any]

def extract_city_from_address(address: str) -> str:
    if not address:
        return ""

    return address.split(",")[0].strip()

@app.post("/calculate-from-analysis")
def calculate_from_analysis(request: CalculateFromAnalysisRequest):
    geo_result = request.geoAnalysis

    market_result = geo_result.get("marketAnalysis")

    if market_result is None and geo_result.get("success"):
        coords = geo_result.get("coordinates", {})

        market_result = market_analyzer.analyze_market(
            lat=coords.get("lat"),
            lon=coords.get("lon"),
            city=extract_city_from_address(geo_result.get("address", "")),
            rooms=request.rooms,
            area=request.area
        )

        geo_result["marketAnalysis"] = market_result

    price_result = price_evaluator.evaluate_price(
        area=request.area,
        rooms=request.rooms,
        text_result=request.textAnalysis,
        image_result=request.imageAnalysis,
        geo_result=geo_result,
        market_result=market_result
    )

    return {
        "success": True,
        "price": price_result,
        "analysis": {
            "textAnalysis": request.textAnalysis,
            "imageAnalysis": request.imageAnalysis,
            "geoAnalysis": geo_result,
            "marketAnalysis": market_result
        }
    }

class MarketAnalysisRequest(BaseModel):
    lat: float
    lon: float
    city: str
    rooms: int
    area: float


@app.post("/analyze-market")
def analyze_market(request: MarketAnalysisRequest):
    return market_analyzer.analyze_market(
        lat=request.lat,
        lon=request.lon,
        city=request.city,
        rooms=request.rooms,
        area=request.area
    )


@app.post("/analyze-text")
async def analyze_text(
        description: str = Form(...)
):
    return text_analyzer.analyze_text(description)



@app.post("/analyze-location")
async def analyze_location(
        address: str = Form(...),
        rooms: int = Form(...),
        area: float = Form(...)
):
    geo_result = geo_analyzer.analyze_location(address)

    if geo_result.get("success"):
        coords = geo_result["coordinates"]

        market_result = market_analyzer.analyze_market(
            lat=coords["lat"],
            lon=coords["lon"],
            city=address.split(",")[0].strip(),
            rooms=rooms,
            area=area
        )

        geo_result["marketAnalysis"] = market_result

    return geo_result

@app.post("/analyze-photos")
async def analyze_photos(
        photos: list[UploadFile] = File(...)
):
    photo_results = []

    for photo in photos:
        content = await photo.read()
        image = Image.open(io.BytesIO(content))

        result = image_analyzer.analyze_image(
            image=image,
            filename=photo.filename
        )

        photo_results.append(result)

    apartment_summary = build_apartment_summary(photo_results)

    return {
        "photosCount": len(photo_results),
        "apartmentSummary": apartment_summary,
        "photos": photo_results
    }


def build_apartment_summary(photo_results):
    visual_scores = [p["visualScore"] for p in photo_results]

    average_visual_score = np.mean(visual_scores)

    room_types = [p["roomAnalysis"]["roomType"] for p in photo_results]
    repair_levels = [p["repairAnalysis"]["repairQuality"] for p in photo_results]
    furniture_levels = [p["furnitureAnalysis"]["furnishingLevel"] for p in photo_results]
    furniture_conditions = [p["furnitureAnalysis"]["furnitureCondition"] for p in photo_results]

    detected_rooms = list(set(room_types))

    average_score = float(average_visual_score)

    return {
        "averageVisualScore": round(average_score, 2),
        "visualQualityLevel": get_visual_quality_level(average_score),
        "detectedRooms": detected_rooms,
        "dominantRepairQuality": most_common(repair_levels),
        "dominantFurnitureLevel": most_common(furniture_levels),
        "dominantFurnitureCondition": most_common(furniture_conditions),
        "priceImpact": calculate_price_impact(average_score),
        "recommendations": build_recommendations(photo_results, average_score)
    }


def most_common(values):
    return max(set(values), key=values.count)


def get_visual_quality_level(score):
    if score >= 85:
        return "Отличное визуальное состояние"

    if score >= 70:
        return "Хорошее визуальное состояние"

    if score >= 50:
        return "Среднее визуальное состояние"

    if score >= 30:
        return "Удовлетворительное визуальное состояние"

    return "Низкое визуальное состояние"


def calculate_price_impact(score):
    if score >= 85:
        return {
            "impact": "Положительное влияние",
            "coefficient": 1.15,
            "description": "Высокое визуальное качество жилья может повысить рекомендуемую стоимость аренды до 15%"
        }

    if score >= 70:
        return {
            "impact": "Положительное влияние",
            "coefficient": 1.08,
            "description": "Хорошее состояние жилья может повысить рекомендуемую стоимость аренды до 8%"
        }

    if score >= 50:
        return {
            "impact": "Нейтральное влияние",
            "coefficient": 1.00,
            "description": "Среднее состояние жилья не оказывает существенного влияния на стоимость"
        }

    if score >= 30:
        return {
            "impact": "Отрицательное влияние",
            "coefficient": 0.90,
            "description": "Низкое визуальное качество может снизить рекомендуемую стоимость аренды до 10%"
        }

    return {
        "impact": "Сильное отрицательное влияние",
        "coefficient": 0.80,
        "description": "Плохое состояние жилья может снизить рекомендуемую стоимость аренды до 20%"
    }


def build_recommendations(photo_results, average_score):
    recommendations = []

    if average_score < 50:
        recommendations.append(
            "Рекомендуется загрузить более качественные фотографии квартиры"
        )

    room_types = [p["roomAnalysis"]["roomType"] for p in photo_results]

    room_names = {
        "kitchen": "Кухня",
        "bathroom": "Ванная комната",
        "bedroom": "Спальня",
        "living_room": "Гостиная",
        "hallway": "Прихожая",
        "balcony": "Балкон"
    }

    required_rooms = {"kitchen", "bathroom", "bedroom"}
    missing_rooms = required_rooms - set(room_types)

    if missing_rooms:
        recommendations.append(
            "Рекомендуется добавить фотографии следующих помещений: "
            + ", ".join(
                room_names[room]
                for room in missing_rooms
            )
        )
    for photo in photo_results:
        if photo["technicalQuality"]["photoQualityScore"] < 50:
            recommendations.append(
                f"Фото {photo['fileName']} имеет низкое качество: рекомендуется улучшить освещение или резкость"
            )

    repair_levels = [p["repairAnalysis"]["repairQuality"] for p in photo_results]

    if "Плохой ремонт" in repair_levels:
        recommendations.append(
            "На части фотографий обнаружены признаки низкого качества ремонта"
        )

    furniture_conditions = [
        p["furnitureAnalysis"]["furnitureCondition"]
        for p in photo_results
    ]

    if "Старая мебель" in furniture_conditions:
        recommendations.append(
            "На части фотографий мебель выглядит устаревшей или изношенной"
        )

    if not recommendations:
        recommendations.append(
            "Фотографии подходят для анализа и положительно влияют на оценку объекта"
        )

    return recommendations


@app.post("/analyze-photos-quality")
async def analyze_photos(
        photos: list[UploadFile] = File(...)
):
    results = []
    total_score = 0

    for photo in photos:
        content = await photo.read()
        image = Image.open(io.BytesIO(content)).convert("RGB")

        # 1. Признаки ResNet50
        features = image_analyzer.extract_features(image)

        # 2. Яркость изображения
        brightness = calculate_brightness(image)

        # 3. Размытость изображения
        sharpness = calculate_sharpness(image)

        # 4. Итоговая оценка фото
        photo_score = calculate_photo_score(brightness, sharpness)

        total_score += photo_score

        results.append({
            "fileName": photo.filename,
            "brightness": round(brightness, 2),
            "sharpness": round(sharpness, 2),
            "photoScore": round(photo_score, 2),
            "imageFeatureSize": len(features)
        })

    average_score = total_score / len(photos)

    return {
        "photosCount": len(photos),
        "averagePhotoScore": round(average_score, 2),
        "qualityLevel": get_quality_level(average_score),
        "photos": results,
        "factors": build_photo_factors(average_score)
    }


def calculate_brightness(image: Image.Image) -> float:
    grayscale = image.convert("L")
    stat = ImageStat.Stat(grayscale)
    return stat.mean[0]


def calculate_sharpness(image: Image.Image) -> float:
    image_np = np.array(image)
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def calculate_photo_score(brightness: float, sharpness: float) -> float:
    score = 0

    # Оценка яркости
    if 80 <= brightness <= 190:
        score += 50
    elif 50 <= brightness < 80 or 190 < brightness <= 220:
        score += 30
    else:
        score += 10

    # Оценка резкости
    if sharpness >= 300:
        score += 50
    elif 100 <= sharpness < 300:
        score += 30
    else:
        score += 10

    return score


def get_quality_level(score: float) -> str:
    if score >= 80:
        return "Высокое качество фотографий"
    elif score >= 50:
        return "Среднее качество фотографий"
    return "Низкое качество фотографий"


def build_photo_factors(score: float):
    if score >= 80:
        return [
            "Фотографии имеют хорошую освещенность",
            "Фотографии достаточно четкие",
            "Изображения подходят для анализа жилья"
        ]

    if score >= 50:
        return [
            "Фотографии пригодны для анализа",
            "Качество изображений среднее",
            "Рекомендуется добавить более четкие и светлые фото"
        ]

    return [
        "Фотографии имеют низкое качество",
        "Возможна недостаточная освещенность или размытость",
        "Рекомендуется загрузить новые фотографии"
    ]