from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import RecommendationRequest
from ..crud import get_places_by_city
from ..recommendation import UserProfile, PlaceData, recommend_places

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/")
def get_recommendations(payload: RecommendationRequest, db: Session = Depends(get_db)):
    db_places = get_places_by_city(db, payload.city)

    user = UserProfile(
        preferred_category=payload.preferred_category,
        preferred_subcategory=payload.preferred_subcategory,
        budget_preference=payload.budget_preference,
        user_latitude=payload.user_latitude,
        user_longitude=payload.user_longitude,
    )

    places = [
        PlaceData(
            id=place.id,
            name=place.name,
            category=place.category,
            subcategory=place.subcategory or "",
            description=place.description or "",
            neighborhood=place.neighborhood or "",
            average_price_level=place.average_price_level or 2,
            average_rating=place.average_rating or 0.0,
            latitude=place.latitude or 0.0,
            longitude=place.longitude or 0.0,
        )
        for place in db_places
    ]

    return recommend_places(user, places, top_n=5)