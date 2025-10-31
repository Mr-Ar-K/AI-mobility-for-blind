import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict
from ..db import database, models, schemas

router = APIRouter(
    prefix="/history",
    tags=["History"]
)

@router.get("/{user_id}", response_model=List[schemas.HistoryItem])
def get_user_history(user_id: int, db: Session = Depends(database.get_db)):
    """
    Get all detection history for a specific user, ordered by date/time (newest first).
    Returns detection results, video paths, audio paths, and timestamps.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return history items in reverse chronological order
    history_items = db.query(models.DetectionHistory)\
                      .filter(models.DetectionHistory.user_id == user_id)\
                      .order_by(models.DetectionHistory.timestamp.desc())\
                      .all()
    
    return history_items


@router.get("/by-username/{username}", response_model=List[schemas.HistoryItem])
def get_user_history_by_username(username: str, db: Session = Depends(database.get_db)):
    """
    Get all detection history for a specific user by username.
    """
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return history items in reverse chronological order
    history_items = db.query(models.DetectionHistory)\
                      .filter(models.DetectionHistory.user_id == user.id)\
                      .order_by(models.DetectionHistory.timestamp.desc())\
                      .all()
    
    return history_items


@router.get("/item/{detection_id}", response_model=schemas.HistoryItem)
def get_detection_by_id(detection_id: int, db: Session = Depends(database.get_db)):
    """
    Get a specific detection history item by its ID.
    """
    detection = db.query(models.DetectionHistory)\
                  .filter(models.DetectionHistory.id == detection_id)\
                  .first()
    
    if not detection:
        raise HTTPException(status_code=404, detail="Detection history not found")
    
    return detection


@router.get("/video/{detection_id}")
def get_detection_video(detection_id: int, db: Session = Depends(database.get_db)):
    """
    Download/stream the video file for a specific detection.
    """
    detection = db.query(models.DetectionHistory)\
                  .filter(models.DetectionHistory.id == detection_id)\
                  .first()
    
    if not detection:
        raise HTTPException(status_code=404, detail="Detection history not found")
    
    if not detection.video_path or not os.path.exists(detection.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        detection.video_path,
        media_type="video/mp4",
        filename=os.path.basename(detection.video_path)
    )


@router.get("/audio/{detection_id}")
def get_detection_audio(detection_id: int, db: Session = Depends(database.get_db)):
    """
    Download/stream the audio file for a specific detection.
    """
    detection = db.query(models.DetectionHistory)\
                  .filter(models.DetectionHistory.id == detection_id)\
                  .first()
    
    if not detection:
        raise HTTPException(status_code=404, detail="Detection history not found")
    
    if not detection.audio_path or not os.path.exists(detection.audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        detection.audio_path,
        media_type="audio/mpeg",
        filename=os.path.basename(detection.audio_path)
    )


@router.get("/image/{detection_id}")
def get_detection_image(detection_id: int, db: Session = Depends(database.get_db)):
    """
    Download/stream the image file for a specific detection.
    """
    detection = db.query(models.DetectionHistory)\
                  .filter(models.DetectionHistory.id == detection_id)\
                  .first()

    if not detection:
        raise HTTPException(status_code=404, detail="Detection history not found")

    if not detection.image_path or not os.path.exists(detection.image_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    # Determine media type based on file extension
    file_ext = os.path.splitext(detection.image_path)[1].lower()
    media_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    media_type = media_type_map.get(file_ext, 'image/jpeg')

    return FileResponse(
        detection.image_path,
        media_type=media_type,
        filename=os.path.basename(detection.image_path)
    )


@router.delete("/{detection_id}")
def delete_detection_history(detection_id: int, db: Session = Depends(database.get_db)):
    """
    Delete a specific detection history item and its associated files.
    """
    detection = db.query(models.DetectionHistory)\
                  .filter(models.DetectionHistory.id == detection_id)\
                  .first()
    
    if not detection:
        raise HTTPException(status_code=404, detail="Detection history not found")

    # Delete associated files
    files_deleted = {"video": False, "image": False, "audio": False}

    if detection.video_path and os.path.exists(detection.video_path):
        try:
            os.remove(detection.video_path)
            files_deleted["video"] = True
        except Exception as e:
            print(f"Failed to delete video file: {e}")

    if detection.image_path and os.path.exists(detection.image_path):
        try:
            os.remove(detection.image_path)
            files_deleted["image"] = True
        except Exception as e:
            print(f"Failed to delete image file: {e}")

    if detection.audio_path and os.path.exists(detection.audio_path):
        try:
            os.remove(detection.audio_path)
            files_deleted["audio"] = True
        except Exception as e:
            print(f"Failed to delete audio file: {e}")
    
    # Delete database entry
    db.delete(detection)
    db.commit()
    
    return {
        "message": "Detection history deleted successfully",
        "files_deleted": files_deleted
    }
