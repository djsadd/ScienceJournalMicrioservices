import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure we load the shared .env from the project root, regardless of working directory.
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://auth:pass@db/auth")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://users:8000")
