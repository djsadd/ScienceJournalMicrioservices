from fastapi import FastAPI
from app.reviews_router import router as reviews_router
from app.database import Base, engine

app = FastAPI(title="Review Service")

# создаем таблицы
Base.metadata.create_all(bind=engine)

app.include_router(reviews_router)
