from dataclasses import dataclass
from typing import List
from math import radians, sin, cos, sqrt, atan2


@dataclass
class UserProfile:
    preferred_category: str
    preferred_subcategory: str
    budget_preference: int
    user_latitude: float
    user_longitude: float


@dataclass
class PlaceData:
    id: int
    name: str
    category: str
    subcategory: str
    description: str
    neighborhood: str
    average_price_level: int
    average_rating: float
    latitude: float
    longitude: float


def calculate_distance_km(user_lat, user_lon, place_lat, place_lon):
    """
    Calcula a distância aproximada em km usando Haversine.
    """
    earth_radius = 6371.0

    dlat = radians(place_lat - user_lat)
    dlon = radians(place_lon - user_lon)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(user_lat)) * cos(radians(place_lat)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return round(earth_radius * c, 2)


def calculate_distance_score(distance_km: float) -> float:
    if distance_km <= 2:
        return 1.0
    if distance_km <= 5:
        return 0.8
    if distance_km <= 10:
        return 0.5
    return 0.2


def calculate_category_score(user, place):
    score = 0.0

    if user.preferred_category.lower() == place.category.lower():
        score += 0.6

    if place.subcategory and user.preferred_subcategory.lower() == place.subcategory.lower():
        score += 0.4

    return min(score, 1.0)


def calculate_price_score(user, place):
    if place.average_price_level is None:
        return 0.5

    difference = abs(user.budget_preference - place.average_price_level)

    if difference == 0:
        return 1.0
    if difference == 1:
        return 0.6
    return 0.2


def normalize_rating(rating):
    if rating is None:
        return 0.5
    return max(0.0, min(rating / 5.0, 1.0))


def get_match_level(score: float) -> str:
    if score >= 0.8:
        return "Alta"
    if score >= 0.6:
        return "Média"
    return "Baixa"


def build_reason(user, place, distance_km, score):
    reasons = []

    if user.preferred_category.lower() == place.category.lower():
        reasons.append(f"combina com sua preferência por {place.category}")

    if place.subcategory and user.preferred_subcategory.lower() == place.subcategory.lower():
        reasons.append(f"tem o estilo que você procura ({place.subcategory})")

    if distance_km <= 5:
        reasons.append("está perto da sua localização")

    if place.average_rating and place.average_rating >= 4.5:
        reasons.append("possui boa avaliação dos usuários")

    if not reasons:
        return "Foi recomendado com base no equilíbrio entre perfil, localização e avaliação."

    return "Recomendado porque " + ", ".join(reasons) + "."


def calculate_final_score(user, place):
    distance_km = calculate_distance_km(
        user.user_latitude,
        user.user_longitude,
        place.latitude or 0.0,
        place.longitude or 0.0,
    )

    category_score = calculate_category_score(user, place)
    price_score = calculate_price_score(user, place)
    distance_score = calculate_distance_score(distance_km)
    rating_score = normalize_rating(place.average_rating)

    final_score = round(
        category_score * 0.4
        + rating_score * 0.3
        + distance_score * 0.2
        + price_score * 0.1,
        4,
    )

    return final_score, distance_km


def recommend_places(user: UserProfile, places: List[PlaceData], top_n: int = 5):
    results = []

    for place in places:
        score, distance_km = calculate_final_score(user, place)

        results.append(
            {
                "id": place.id,
                "name": place.name,
                "category": place.category,
                "subcategory": place.subcategory,
                "description": place.description,
                "neighborhood": place.neighborhood,
                "score": score,
                "match_level": get_match_level(score),
                "rating": place.average_rating,
                "price_level": place.average_price_level,
                "distance_km": distance_km,
                "reason": build_reason(user, place, distance_km, score),
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_n]