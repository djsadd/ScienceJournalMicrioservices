from fastapi import FastAPI
from app.database import Base, engine
from app.router import router as processing_router

app = FastAPI(title="File Processing Service")

Base.metadata.create_all(bind=engine)

app.include_router(processing_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
