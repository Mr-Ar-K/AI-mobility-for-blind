import os
import shutil
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from ultralytics import YOLO

from ..db import database, models, schemas
from ..services import video_processor
from ..core.config import settings

router = APIRouter(
    prefix="/detect",
    tags=["Detection"]
)

# Define the temporary upload directory
TEMP_UPLOAD_DIR = "tmp/"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# Dependency to get the loaded model from app state
def get_model(request: Request):
    return request.app.state.model

@router.post("/{user_id}", response_model=List[str])
async def detect_video(
    user_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    # Get model from app state
    model = request.app.state.model
    
    # 1. Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Save video to a temporary file
    # Create a unique filename to avoid conflicts
    file_extension = os.path.splitext(file.filename)[1]
    temp_filename = f"{uuid.uuid4()}{file_extension}"
    temp_video_path = os.path.join(TEMP_UPLOAD_DIR, temp_filename)

    try:
        with open(temp_video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video file: {e}")
    finally:
        file.file.close()

    # 3. Process the video
    try:
        audio_results_list = video_processor.run_detection(temp_video_path, model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed during video processing: {e}")

    # 4. Save results to history
    try:
        history_entry = models.DetectionHistory(
            user_id=user_id,
            results=audio_results_list
        )
        db.add(history_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to save history: {e}")
        # We don't raise an error here, as the user should still get their results

    # 5. Clean up the temporary video
    try:
        os.remove(temp_video_path)
    except Exception as e:
        print(f"Warning: Failed to delete temporary file {temp_video_path}: {e}")

    # 6. Return the audio strings to the frontend
    return audio_results_list
