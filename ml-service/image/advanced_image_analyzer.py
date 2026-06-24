import cv2
import torch
import numpy as np
from PIL import Image, ImageStat
from torchvision import models, transforms
from ultralytics import YOLO
from transformers import CLIPProcessor, CLIPModel


class AdvancedImageAnalyzer:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.resnet = models.resnet50(
            weights=models.ResNet50_Weights.DEFAULT
        )
        self.resnet.fc = torch.nn.Identity()
        self.resnet.to(self.device)
        self.resnet.eval()

        self.resnet_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        self.yolo = YOLO("../yolov8n.pt")

        self.clip_model = CLIPModel.from_pretrained(
            "openai/clip-vit-base-patch32"
        ).to(self.device)

        self.clip_processor = CLIPProcessor.from_pretrained(
            "openai/clip-vit-base-patch32"
        )

        self.room_translations = {
            "kitchen": "Кухня",
            "bedroom": "Спальня",
            "living_room": "Гостиная",
            "bathroom": "Ванная комната",
            "hallway": "Прихожая",
            "balcony": "Балкон"
        }

        self.repair_translations = {
            "poor": "Плохой ремонт",
            "basic": "Обычный ремонт",
            "good": "Хороший ремонт",
            "premium": "Премиальный ремонт"
        }

        self.furniture_translations = {
            "no_furniture": "Без мебели",
            "old_furniture": "Старая мебель",
            "average_furniture": "Обычная мебель",
            "new_furniture": "Новая мебель",
            "premium_furniture": "Премиальная мебель"
        }

        self.furnishing_translations = {
            "empty": "Без мебели",
            "low": "Низкая наполненность",
            "medium": "Средняя наполненность",
            "high": "Высокая наполненность"
        }

        self.style_translations = {
            "old_style": "Устаревший интерьер",
            "standard": "Стандартный интерьер",
            "modern": "Современный интерьер",
            "minimalist": "Минималистичный интерьер",
            "luxury": "Элитный интерьер"
        }

        self.cleanliness_translations = {
            "dirty": "Грязно",
            "normal": "Чисто",
            "very_clean": "Очень чисто"
        }

        self.object_translations = {
            "chair": "Стул",
            "couch": "Диван",
            "bed": "Кровать",
            "dining table": "Обеденный стол",
            "tv": "Телевизор",
            "refrigerator": "Холодильник",
            "oven": "Духовка",
            "microwave": "Микроволновая печь",
            "sink": "Раковина",
            "toilet": "Унитаз",
            "potted plant": "Комнатное растение",
            "book": "Книга",
            "clock": "Часы"
        }

    def analyze_image(self, image: Image.Image, filename: str):
        image = image.convert("RGB")

        brightness = self.calculate_brightness(image)
        sharpness = self.calculate_sharpness(image)

        image_features = self.extract_resnet_features(image)
        detected_objects = self.detect_objects(image)

        room_type = self.classify_with_clip(image, {
            "kitchen": "a photo of a kitchen",
            "bedroom": "a photo of a bedroom",
            "living_room": "a photo of a living room",
            "bathroom": "a photo of a bathroom",
            "hallway": "a photo of a hallway",
            "balcony": "a photo of a balcony"
        })

        repair_quality = self.classify_with_clip(image, {
            "poor": "an old apartment with poor renovation",
            "basic": "an apartment with basic renovation",
            "good": "an apartment with good modern renovation",
            "premium": "a luxury apartment with premium renovation"
        })

        furniture_condition = self.classify_with_clip(image, {
            "no_furniture": "an empty room without furniture",
            "old_furniture": "a room with old worn furniture",
            "average_furniture": "a room with average furniture",
            "new_furniture": "a room with new modern furniture",
            "premium_furniture": "a room with expensive premium furniture"
        })

        interior_style = self.classify_with_clip(image, {
            "old_style": "old outdated interior",
            "standard": "standard apartment interior",
            "modern": "modern apartment interior",
            "minimalist": "minimalist apartment interior",
            "luxury": "luxury expensive apartment interior"
        })

        cleanliness = self.classify_with_clip(image, {
            "dirty": "dirty messy apartment room",
            "normal": "normal clean apartment room",
            "very_clean": "very clean tidy apartment room"
        })

        furnishing_level = self.calculate_furnishing_level(detected_objects)

        photo_quality_score = self.calculate_photo_quality_score(
            brightness,
            sharpness
        )

        visual_score = self.calculate_visual_score(
            photo_quality_score=photo_quality_score,
            repair_quality=repair_quality["label"],
            furniture_condition=furniture_condition["label"],
            furnishing_level=furnishing_level["level"],
            cleanliness=cleanliness["label"],
            interior_style=interior_style["label"]
        )

        return {
            "fileName": filename,
            "technicalQuality": {
                "brightness": round(brightness, 2),
                "sharpness": round(sharpness, 2),
                "photoQualityScore": round(photo_quality_score, 2)
            },
            "roomAnalysis": {
                "roomType": self.translate(room_type["label"], self.room_translations),
                "confidence": round(room_type["confidence"], 3)
            },
            "repairAnalysis": {
                "repairQuality": self.translate(repair_quality["label"], self.repair_translations),
                "confidence": round(repair_quality["confidence"], 3)
            },
            "furnitureAnalysis": {
                "furnitureCondition": self.translate(
                    furniture_condition["label"],
                    self.furniture_translations
                ),
                "furnishingLevel": self.translate(
                    furnishing_level["level"],
                    self.furnishing_translations
                ),
                "furnitureObjectsCount": furnishing_level["count"],
                "confidence": round(furniture_condition["confidence"], 3)
            },
            "interiorAnalysis": {
                "style": self.translate(interior_style["label"], self.style_translations),
                "cleanliness": self.translate(cleanliness["label"], self.cleanliness_translations),
                "styleConfidence": round(interior_style["confidence"], 3),
                "cleanlinessConfidence": round(cleanliness["confidence"], 3)
            },
            "detectedObjects": detected_objects,
            "visualScore": round(visual_score, 2),
            "imageFeatureSize": len(image_features)
        }

    def translate(self, value: str, dictionary: dict):
        return dictionary.get(value, value)

    def extract_resnet_features(self, image: Image.Image):
        tensor = self.resnet_transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            features = self.resnet(tensor)

        return features.squeeze().cpu().numpy()

    def detect_objects(self, image: Image.Image):
        image_np = np.array(image)

        results = self.yolo(image_np, verbose=False)

        detected = []

        target_classes = {
            "chair",
            "couch",
            "bed",
            "dining table",
            "tv",
            "refrigerator",
            "oven",
            "microwave",
            "sink",
            "toilet",
            "potted plant",
            "book",
            "clock"
        }

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = self.yolo.names[class_id]
                confidence = float(box.conf[0])

                if class_name in target_classes and confidence >= 0.35:
                    detected.append({
                        "object": self.translate(class_name, self.object_translations),
                        "confidence": round(confidence, 3)
                    })

        return detected

    def classify_with_clip(self, image: Image.Image, labels: dict):
        texts = list(labels.values())
        keys = list(labels.keys())

        inputs = self.clip_processor(
            text=texts,
            images=image,
            return_tensors="pt",
            padding=True
        ).to(self.device)

        with torch.no_grad():
            outputs = self.clip_model(**inputs)
            logits = outputs.logits_per_image
            probs = logits.softmax(dim=1).cpu().numpy()[0]

        best_index = int(np.argmax(probs))

        return {
            "label": keys[best_index],
            "confidence": float(probs[best_index])
        }

    def calculate_brightness(self, image: Image.Image) -> float:
        grayscale = image.convert("L")
        stat = ImageStat.Stat(grayscale)
        return stat.mean[0]

    def calculate_sharpness(self, image: Image.Image) -> float:
        image_np = np.array(image)
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    def calculate_photo_quality_score(self, brightness: float, sharpness: float):
        score = 0

        if 80 <= brightness <= 190:
            score += 50
        elif 50 <= brightness < 80 or 190 < brightness <= 220:
            score += 30
        else:
            score += 10

        if sharpness >= 300:
            score += 50
        elif 100 <= sharpness < 300:
            score += 30
        else:
            score += 10

        return score

    def calculate_furnishing_level(self, detected_objects):
        furniture_names = {
            "Стул",
            "Диван",
            "Кровать",
            "Обеденный стол",
            "Телевизор",
            "Холодильник",
            "Духовка",
            "Микроволновая печь",
            "Раковина",
            "Унитаз"
        }

        furniture_objects = [
            obj for obj in detected_objects
            if obj["object"] in furniture_names
        ]

        count = len(furniture_objects)

        if count == 0:
            level = "empty"
        elif count <= 2:
            level = "low"
        elif count <= 5:
            level = "medium"
        else:
            level = "high"

        return {
            "level": level,
            "count": count
        }

    def calculate_visual_score(
            self,
            photo_quality_score,
            repair_quality,
            furniture_condition,
            furnishing_level,
            cleanliness,
            interior_style
    ):
        score = 0

        score += photo_quality_score * 0.2

        repair_scores = {
            "poor": 10,
            "basic": 35,
            "good": 70,
            "premium": 100
        }

        furniture_scores = {
            "no_furniture": 20,
            "old_furniture": 30,
            "average_furniture": 55,
            "new_furniture": 80,
            "premium_furniture": 100
        }

        furnishing_scores = {
            "empty": 20,
            "low": 40,
            "medium": 70,
            "high": 90
        }

        cleanliness_scores = {
            "dirty": 20,
            "normal": 70,
            "very_clean": 100
        }

        style_scores = {
            "old_style": 25,
            "standard": 55,
            "modern": 80,
            "minimalist": 75,
            "luxury": 100
        }

        score += repair_scores.get(repair_quality, 50) * 0.3
        score += furniture_scores.get(furniture_condition, 50) * 0.2
        score += furnishing_scores.get(furnishing_level, 50) * 0.15
        score += cleanliness_scores.get(cleanliness, 50) * 0.1
        score += style_scores.get(interior_style, 50) * 0.05

        return score