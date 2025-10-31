import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Get the backend directory path (where .env should be)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str
    # Three model paths for the multi-model detection system
    MODEL_PATH_YOLO: str = "models/yolov8m.pt"
    MODEL_PATH_TRAFFIC_LIGHTS: str = "models/traffic lights.pt"
    MODEL_PATH_ZEBRA_CROSSING: str = "models/zebra crossing.pt"
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
