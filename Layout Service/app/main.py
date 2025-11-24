import os
from fastapi import FastAPI

FILE_SERVICE_URL = os.getenv("FILE_SERVICE_URL", "http://fileprocessing:7000")

app = FastAPI(title="Layout Service")


@app.get("/health")
async def health():
    return {"status": "ok", "file_service": FILE_SERVICE_URL}
