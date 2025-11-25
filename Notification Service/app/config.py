import os
from pathlib import Path
from dotenv import load_dotenv

# Load shared .env from project root so SECRET_KEY and DB URLs are consistent
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://notifications:pass@db/notifications")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"

