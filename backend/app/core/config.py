from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    # Three model paths for the multi-model detection system
    MODEL_PATH_YOLO: str = "models/yolov8m.pt"
    MODEL_PATH_TRAFFIC_LIGHTS: str = "models/traffic lights.pt"
    MODEL_PATH_ZEBRA_CROSSING: str = "models/zebra crossing.pt"
    Backend_PORT: str = "http://localhost:8000"
    Backend_PORT_FALLBACK: str = "http://0.0.0.0:8000"

    class Config:
        env_file = ".env"

settings = Settings()
