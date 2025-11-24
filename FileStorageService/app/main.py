import os
from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.router import router
from app import config


def ensure_storage():
    os.makedirs(config.STORAGE_PATH, exist_ok=True)


ensure_storage()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="File Storage Service")
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}
