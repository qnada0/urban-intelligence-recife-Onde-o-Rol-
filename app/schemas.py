from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    name: str
    email: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None
    budget_preference: Optional[str] = None


class UserResponse(UserCreate):
    id: int

    class Config:
        from_attributes = True


class PlaceCreate(BaseModel):
    name: str
    category: str
    subcategory: Optional[str] = None
    description: Optional[str] = None
    neighborhood: Optional[str] = None
    city: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    average_price_level: Optional[int] = None
    average_rating: Optional[float] = None
    total_reviews: Optional[int] = None
    source: Optional[str] = None


class PlaceResponse(PlaceCreate):
    id: int

    class Config:
        from_attributes = True


class RecommendationRequest(BaseModel):
    preferred_category: str
    preferred_subcategory: str
    budget_preference: int
    user_latitude: float
    user_longitude: float
    city: str