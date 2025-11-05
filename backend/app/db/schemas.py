from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Detection History Schemas ---

class HistoryItemBase(BaseModel):
    results: List[str]

class HistoryItemCreate(HistoryItemBase):
    pass

class HistoryItem(HistoryItemBase):
    id: int
    timestamp: datetime
    video_path: Optional[str] = None
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
    media_type: str = "video"
    user_id: int

    class Config:
        from_attributes = True

# --- User Schemas ---

class UserBase(BaseModel):
    username: str
    email: str
    language: Optional[str] = 'en'  # Default to English

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    language: Optional[str] = None

class User(UserBase):
    id: int
    history_items: List[HistoryItem] = []

    class Config:
        from_attributes = True
