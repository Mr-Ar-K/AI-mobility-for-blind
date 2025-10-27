from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    MODEL_PATH: str
    Backend_PORT: str = "http://localhost:8000"
    Backend_PORT_FALLBACK: str = "http://0.0.0.0:8000"

    class Config:
        env_file = ".env"

settings = Settings()
