from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.router import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Editorial Workflow Service")
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}
