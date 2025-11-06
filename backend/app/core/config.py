"""
Backend Configuration Settings

Loads environment variables from .env file using Pydantic Settings.
Supports multi-language TTS, async video processing, and H.264 video encoding.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Get the backend directory path (where .env should be)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"

class Settings(BaseSettings):
    """
    Application Settings
    
    Environment Variables:
    - DATABASE_URL: PostgreSQL connection string (includes user language preferences)
    - MODEL_PATH: Path to custom YOLOv8n model (Car, Person, Green Light, zebra crossing)
    - Backend_PORT: Primary backend URL for API requests
    - Backend_PORT_FALLBACK: Fallback backend URL
    - HISTORY_STORAGE_DIR: Directory for storing detection results (videos/images/audio)
    - TEMP_UPLOAD_DIR: Temporary directory for file uploads
    
    Additional Features (handled in service layer):
    - Multi-language TTS: English, Telugu (te), Hindi (hi)
    - H.264 High Profile Level 4.1 video encoding
    - Async detection with real-time progress tracking
    - Adjustable audio playback speed (0.5x - 2x)
    """
    
    # Database Configuration
    # PostgreSQL with user language preferences stored in users.language column
    DATABASE_URL: str
    
    # Custom YOLOv8n Model
    # Single model detects 4 classes: Car, Person, Green Light, zebra crossing
    # Model file should be approximately 6-10 MB
    MODEL_PATH: str = "models/Yolov8n.pt"
    
    # Backend Server URLs
    # Primary and fallback URLs for API communication
    Backend_PORT: str = "http://localhost:8000"
    Backend_PORT_FALLBACK: str = "http://0.0.0.0:8000"
    
    # Storage Directories
    # Files organized by username/date/time structure
    # Auto-created if they don't exist
    HISTORY_STORAGE_DIR: str = "storage/history"
    TEMP_UPLOAD_DIR: str = "tmp/"

    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = 'utf-8'
        extra = "ignore"  # Ignore extra fields from old .env files
        case_sensitive = False  # Allow case-insensitive env var names

# Global settings instance
settings = Settings()
