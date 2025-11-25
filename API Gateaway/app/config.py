import os
from pathlib import Path
from dotenv import load_dotenv

# Load shared .env from project root so SECRET_KEY is consistent
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

SERVICE_URLS = {
    "auth": "http://auth:8000",
    "users": "http://users:8000",
    "articles": "http://articles:8000",
    "reviews": "http://reviews:8000",
    "editorial": "http://editorial:8000",
    "layout": "http://layout:8000",
    "publication": "http://publication:8000",
    "notifications": "http://notifications:8000",
    "analytics": "http://analytics:8000",
    "files": "http://fileprocessing:7000",
}

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
