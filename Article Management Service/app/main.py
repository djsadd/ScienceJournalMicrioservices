from fastapi import FastAPI
from app.articles_router import router as articles_router
from app.database import Base, engine
from app import models  # register models for metadata

app = FastAPI(title="Article Management Service")

# init tables
Base.metadata.create_all(bind=engine)

app.include_router(articles_router)
