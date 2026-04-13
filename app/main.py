from fastapi import FastAPI
from .database import Base, engine
from .routers import users, places, recommendations

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Urban Intelligence API",
    description="API para recomendação de experiências urbanas",
    version="1.0.0",
)

app.include_router(users.router)
app.include_router(places.router)
app.include_router(recommendations.router)


@app.get("/")
def root():
    return {"message": "Urban Intelligence API running successfully"}