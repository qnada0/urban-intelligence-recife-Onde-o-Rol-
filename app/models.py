from sqlalchemy import Column, Integer, String, Float, Text
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=True)
    age = Column(Integer, nullable=True)
    city = Column(String(100), nullable=True)
    budget_preference = Column(String(20), nullable=True)


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)
    subcategory = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    neighborhood = Column(String(100), nullable=True)
    city = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    average_price_level = Column(Integer, nullable=True)
    average_rating = Column(Float, nullable=True)
    total_reviews = Column(Integer, nullable=True)
    source = Column(String(50), nullable=True)