import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Get the backend directory path (where .env should be)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str
    # Single custom model path for 4-class detection: Car, Person, Green Light, zebra crossing
    MODEL_PATH: str = "models/Yolov8n.pt"
    Backend_PORT: str = "http://localhost:8000"
    Backend_PORT_FALLBACK: str = "http://0.0.0.0:8000"
    # Storage paths for history files
    HISTORY_STORAGE_DIR: str = "storage/history"
    TEMP_UPLOAD_DIR: str = "tmp/"

    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = 'utf-8'
        extra = "ignore"  # Ignore extra fields from old .env files

settings = Settings()
