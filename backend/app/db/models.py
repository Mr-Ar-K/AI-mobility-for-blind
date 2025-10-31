from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # Plain text for prototype

    history_items = relationship("DetectionHistory", back_populates="owner")

class DetectionHistory(Base):
    __tablename__ = "detection_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    results = Column(JSON, nullable=False)  # Stores the list of text strings
    video_path = Column(String, nullable=True)  # Path to saved video file
    image_path = Column(String, nullable=True)  # Path to saved image file
    audio_path = Column(String, nullable=True)  # Path to generated audio file
    media_type = Column(String, nullable=False, default="video")  # "video" or "image"

    owner = relationship("User", back_populates="history_items")
