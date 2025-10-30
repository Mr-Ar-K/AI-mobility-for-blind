import os
import shutil
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict
from ultralytics import YOLO

from ..db import database, models, schemas
from ..services import video_processor, audio_generator
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
    # Get all three models from app state
    model_yolo = request.app.state.model_yolo
    model_lights = request.app.state.model_lights
    model_zebra = request.app.state.model_zebra
    
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

    # 3. Process the video with all three models
    try:
        audio_results_list = video_processor.run_detection(
            temp_video_path, 
            model_yolo, 
            model_lights, 
            model_zebra
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed during video processing: {e}")
    
    # 3.5. Generate audio file from detection results
    audio_file_path = None
    try:
        generator = audio_generator.AudioGenerator(pause_duration=700)
        audio_file_path = generator.generate_audio_quick(audio_results_list)
        print(f"Audio generated: {audio_file_path}")
    except Exception as e:
        print(f"Warning: Failed to generate audio: {e}")
        # Continue even if audio generation fails

    # 4. Save results to history (including audio path if available)
    try:
        history_entry = models.DetectionHistory(
            user_id=user_id,
            results=audio_results_list,
            audio_path=audio_file_path
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


@router.post("/{user_id}/with-audio", response_model=Dict)
async def detect_video_with_audio(
    user_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    """
    Process video and return both text results and audio file path.
    This endpoint is useful when you need the audio file immediately.
    """
    # Get all three models from app state
    model_yolo = request.app.state.model_yolo
    model_lights = request.app.state.model_lights
    model_zebra = request.app.state.model_zebra
    
    # 1. Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Save video to a temporary file
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

    # 3. Process the video with all three models
    try:
        audio_results_list = video_processor.run_detection(
            temp_video_path, 
            model_yolo, 
            model_lights, 
            model_zebra
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed during video processing: {e}")
    
    # 4. Generate audio file from detection results
    audio_file_path = None
    try:
        generator = audio_generator.AudioGenerator(pause_duration=700)
        audio_file_path = generator.generate_audio_quick(audio_results_list)
        print(f"Audio generated: {audio_file_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {e}")

    # 5. Save results to history
    try:
        history_entry = models.DetectionHistory(
            user_id=user_id,
            results=audio_results_list,
            audio_path=audio_file_path
        )
        db.add(history_entry)
        db.commit()
        db.refresh(history_entry)
        detection_id = history_entry.id
    except Exception as e:
        db.rollback()
        print(f"Failed to save history: {e}")
        detection_id = None

    # 6. Clean up the temporary video
    try:
        os.remove(temp_video_path)
    except Exception as e:
        print(f"Warning: Failed to delete temporary file {temp_video_path}: {e}")

    # 7. Return both text results and audio file info
    return {
        "text_results": audio_results_list,
        "audio_file": os.path.basename(audio_file_path) if audio_file_path else None,
        "audio_url": f"/detect/audio/{os.path.basename(audio_file_path)}" if audio_file_path else None,
        "detection_id": detection_id
    }


@router.get("/audio/{audio_filename}")
async def get_audio_file(audio_filename: str):
    """
    Download/stream the generated audio file.
    """
    audio_path = os.path.join(TEMP_UPLOAD_DIR, audio_filename)
    
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        audio_path, 
        media_type="audio/mpeg",
        filename=audio_filename
    )


@router.post("/generate-audio")
async def generate_audio_from_text(text_list: List[str]):
    """
    Generate audio from a list of text strings.
    Useful for testing or generating audio from saved results.
    """
    try:
        generator = audio_generator.AudioGenerator(pause_duration=700)
        audio_path = generator.generate_audio_quick(text_list)
        
        return {
            "success": True,
            "audio_file": os.path.basename(audio_path),
            "audio_url": f"/detect/audio/{os.path.basename(audio_path)}",
            "message": "Audio generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")
