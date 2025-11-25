from fastapi import FastAPI
from app.notifications_router import router as notifications_router
from app.database import Base, engine

app = FastAPI(title="Notification Service")

# Initialize database tables
Base.metadata.create_all(bind=engine)

app.include_router(notifications_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
