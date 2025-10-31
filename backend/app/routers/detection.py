import os
import shutil
import uuid
from datetime import datetime
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

# Define the temporary upload directory and history storage
TEMP_UPLOAD_DIR = settings.TEMP_UPLOAD_DIR
HISTORY_STORAGE_DIR = settings.HISTORY_STORAGE_DIR
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
os.makedirs(HISTORY_STORAGE_DIR, exist_ok=True)

def get_user_storage_path(username: str, timestamp: datetime) -> str:
    """
    Create and return a storage path organized by username and date/time.
    Format: storage/history/{username}/{YYYY-MM-DD}/{HH-MM-SS}/
    """
    date_str = timestamp.strftime("%Y-%m-%d")
    time_str = timestamp.strftime("%H-%M-%S")
    user_dir = os.path.join(HISTORY_STORAGE_DIR, username, date_str, time_str)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

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
    
    # 3.5. Get timestamp and create user storage directory
    detection_timestamp = datetime.now()
    user_storage_dir = get_user_storage_path(user.username, detection_timestamp)
    
    # 3.6. Generate audio file and save to user's directory
    saved_audio_path = None
    try:
        generator = audio_generator.AudioGenerator(pause_duration=700)
        temp_audio_path = generator.generate_audio_quick(audio_results_list)
        
        # Move audio to permanent storage
        audio_filename = f"audio_{detection_timestamp.strftime('%H-%M-%S')}.mp3"
        saved_audio_path = os.path.join(user_storage_dir, audio_filename)
        shutil.move(temp_audio_path, saved_audio_path)
        print(f"Audio saved to: {saved_audio_path}")
    except Exception as e:
        print(f"Warning: Failed to generate/save audio: {e}")
        # Continue even if audio generation fails

    # 3.7. Save video to user's directory
    saved_video_path = None
    try:
        video_filename = f"video_{detection_timestamp.strftime('%H-%M-%S')}{file_extension}"
        saved_video_path = os.path.join(user_storage_dir, video_filename)
        shutil.copy2(temp_video_path, saved_video_path)
        print(f"Video saved to: {saved_video_path}")
    except Exception as e:
        print(f"Warning: Failed to save video to history: {e}")

    # 4. Save results to history (including video and audio paths)
    try:
        history_entry = models.DetectionHistory(
            user_id=user_id,
            results=audio_results_list,
            video_path=saved_video_path,
            audio_path=saved_audio_path
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
    
    # 4. Get timestamp and create user storage directory
    detection_timestamp = datetime.now()
    user_storage_dir = get_user_storage_path(user.username, detection_timestamp)
    
    # 5. Generate audio file and save to user's directory
    saved_audio_path = None
    try:
        generator = audio_generator.AudioGenerator(pause_duration=700)
        temp_audio_path = generator.generate_audio_quick(audio_results_list)
        
        # Move audio to permanent storage
        audio_filename = f"audio_{detection_timestamp.strftime('%H-%M-%S')}.mp3"
        saved_audio_path = os.path.join(user_storage_dir, audio_filename)
        shutil.move(temp_audio_path, saved_audio_path)
        print(f"Audio saved to: {saved_audio_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {e}")

    # 6. Save video to user's directory
    saved_video_path = None
    try:
        video_filename = f"video_{detection_timestamp.strftime('%H-%M-%S')}{file_extension}"
        saved_video_path = os.path.join(user_storage_dir, video_filename)
        shutil.copy2(temp_video_path, saved_video_path)
        print(f"Video saved to: {saved_video_path}")
    except Exception as e:
        print(f"Warning: Failed to save video to history: {e}")

    # 7. Save results to history
    try:
        history_entry = models.DetectionHistory(
            user_id=user_id,
            results=audio_results_list,
            video_path=saved_video_path,
            audio_path=saved_audio_path
        )
        db.add(history_entry)
        db.commit()
        db.refresh(history_entry)
        detection_id = history_entry.id
    except Exception as e:
        db.rollback()
        print(f"Failed to save history: {e}")
        detection_id = None

    # 8. Clean up the temporary video
    try:
        os.remove(temp_video_path)
    except Exception as e:
        print(f"Warning: Failed to delete temporary file {temp_video_path}: {e}")

    # 9. Return both text results and audio file info
    return {
        "text_results": audio_results_list,
        "audio_file": os.path.basename(saved_audio_path) if saved_audio_path else None,
        "audio_url": f"/history/audio/{detection_id}" if detection_id else None,
        "video_url": f"/history/video/{detection_id}" if detection_id else None,
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


    @router.post("/image/{user_id}", response_model=List[str])
    async def detect_image(
        user_id: int,
        request: Request,
        file: UploadFile = File(...),
        db: Session = Depends(database.get_db)
    ):
        """
        Process an uploaded image and detect objects.
        Saves the image and audio to history.
        """
        # Get all three models from app state
        model_yolo = request.app.state.model_yolo
        model_lights = request.app.state.model_lights
        model_zebra = request.app.state.model_zebra
    
        # 1. Check if user exists
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 2. Save image to a temporary file
        file_extension = os.path.splitext(file.filename)[1]
        if file_extension.lower() not in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
            raise HTTPException(status_code=400, detail="Invalid image format. Supported: jpg, jpeg, png, bmp, webp")
    
        temp_filename = f"{uuid.uuid4()}{file_extension}"
        temp_image_path = os.path.join(TEMP_UPLOAD_DIR, temp_filename)

        try:
            with open(temp_image_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save image file: {e}")
        finally:
            file.file.close()

        # 3. Run detection on the image
        try:
            # Run all three models on the image
            detections = []
        
            # YOLO general object detection
            results_yolo = model_yolo(temp_image_path)
            for result in results_yolo:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    if confidence > 0.5:  # Confidence threshold
                        class_name = result.names[class_id]
                        detections.append(f"{class_name} detected")
        
            # Traffic lights detection
            results_lights = model_lights(temp_image_path)
            for result in results_lights:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    if confidence > 0.5:
                        class_name = result.names[class_id]
                        detections.append(f"traffic light {class_name}")
        
            # Zebra crossing detection
            results_zebra = model_zebra(temp_image_path)
            for result in results_zebra:
                for box in result.boxes:
                    confidence = float(box.conf[0])
                    if confidence > 0.5:
                        detections.append("zebra crossing detected")
                        break
        
            # Remove duplicates and create audio results
            audio_results_list = list(set(detections)) if detections else ["no objects detected"]
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed during image processing: {e}")
    
        # 4. Get timestamp and create user storage directory
        detection_timestamp = datetime.now()
        user_storage_dir = get_user_storage_path(user.username, detection_timestamp)
    
        # 5. Generate audio file and save to user's directory
        saved_audio_path = None
        try:
            generator = audio_generator.AudioGenerator(pause_duration=700)
            temp_audio_path = generator.generate_audio_quick(audio_results_list)
        
            # Move audio to permanent storage
            audio_filename = f"audio_{detection_timestamp.strftime('%H-%M-%S')}.mp3"
            saved_audio_path = os.path.join(user_storage_dir, audio_filename)
            shutil.move(temp_audio_path, saved_audio_path)
            print(f"Audio saved to: {saved_audio_path}")
        except Exception as e:
            print(f"Warning: Failed to generate/save audio: {e}")

        # 6. Save image to user's directory
        saved_image_path = None
        try:
            image_filename = f"image_{detection_timestamp.strftime('%H-%M-%S')}{file_extension}"
            saved_image_path = os.path.join(user_storage_dir, image_filename)
            shutil.copy2(temp_image_path, saved_image_path)
            print(f"Image saved to: {saved_image_path}")
        except Exception as e:
            print(f"Warning: Failed to save image to history: {e}")

        # 7. Save results to history (including image and audio paths)
        try:
            history_entry = models.DetectionHistory(
                user_id=user_id,
                results=audio_results_list,
                image_path=saved_image_path,
                audio_path=saved_audio_path,
                media_type="image"
            )
            db.add(history_entry)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Failed to save history: {e}")

        # 8. Clean up the temporary image
        try:
            os.remove(temp_image_path)
        except Exception as e:
            print(f"Warning: Failed to delete temporary file {temp_image_path}: {e}")

        # 9. Return the detection results to the frontend
        return audio_results_list


    @router.post("/image/{user_id}/with-audio", response_model=Dict)
    async def detect_image_with_audio(
        user_id: int,
        request: Request,
        file: UploadFile = File(...),
        db: Session = Depends(database.get_db)
    ):
        """
        Process image and return both text results and audio file path.
        """
        # Get all three models from app state
        model_yolo = request.app.state.model_yolo
        model_lights = request.app.state.model_lights
        model_zebra = request.app.state.model_zebra
    
        # 1. Check if user exists
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 2. Save image to a temporary file
        file_extension = os.path.splitext(file.filename)[1]
        if file_extension.lower() not in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
            raise HTTPException(status_code=400, detail="Invalid image format. Supported: jpg, jpeg, png, bmp, webp")
    
        temp_filename = f"{uuid.uuid4()}{file_extension}"
        temp_image_path = os.path.join(TEMP_UPLOAD_DIR, temp_filename)

        try:
            with open(temp_image_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save image file: {e}")
        finally:
            file.file.close()

        # 3. Run detection on the image
        try:
            detections = []
        
            # YOLO general object detection
            results_yolo = model_yolo(temp_image_path)
            for result in results_yolo:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    if confidence > 0.5:
                        class_name = result.names[class_id]
                        detections.append(f"{class_name} detected")
        
            # Traffic lights detection
            results_lights = model_lights(temp_image_path)
            for result in results_lights:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    if confidence > 0.5:
                        class_name = result.names[class_id]
                        detections.append(f"traffic light {class_name}")
        
            # Zebra crossing detection
            results_zebra = model_zebra(temp_image_path)
            for result in results_zebra:
                for box in result.boxes:
                    confidence = float(box.conf[0])
                    if confidence > 0.5:
                        detections.append("zebra crossing detected")
                        break
        
            audio_results_list = list(set(detections)) if detections else ["no objects detected"]
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed during image processing: {e}")
    
        # 4. Get timestamp and create user storage directory
        detection_timestamp = datetime.now()
        user_storage_dir = get_user_storage_path(user.username, detection_timestamp)
    
        # 5. Generate audio file and save to user's directory
        saved_audio_path = None
        try:
            generator = audio_generator.AudioGenerator(pause_duration=700)
            temp_audio_path = generator.generate_audio_quick(audio_results_list)
        
            audio_filename = f"audio_{detection_timestamp.strftime('%H-%M-%S')}.mp3"
            saved_audio_path = os.path.join(user_storage_dir, audio_filename)
            shutil.move(temp_audio_path, saved_audio_path)
            print(f"Audio saved to: {saved_audio_path}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate audio: {e}")

        # 6. Save image to user's directory
        saved_image_path = None
        try:
            image_filename = f"image_{detection_timestamp.strftime('%H-%M-%S')}{file_extension}"
            saved_image_path = os.path.join(user_storage_dir, image_filename)
            shutil.copy2(temp_image_path, saved_image_path)
            print(f"Image saved to: {saved_image_path}")
        except Exception as e:
            print(f"Warning: Failed to save image to history: {e}")

        # 7. Save results to history
        try:
            history_entry = models.DetectionHistory(
                user_id=user_id,
                results=audio_results_list,
                image_path=saved_image_path,
                audio_path=saved_audio_path,
                media_type="image"
            )
            db.add(history_entry)
            db.commit()
            db.refresh(history_entry)
            detection_id = history_entry.id
        except Exception as e:
            db.rollback()
            print(f"Failed to save history: {e}")
            detection_id = None

        # 8. Clean up the temporary image
        try:
            os.remove(temp_image_path)
        except Exception as e:
            print(f"Warning: Failed to delete temporary file {temp_image_path}: {e}")

        # 9. Return both text results and file info
        return {
            "text_results": audio_results_list,
            "audio_file": os.path.basename(saved_audio_path) if saved_audio_path else None,
            "audio_url": f"/history/audio/{detection_id}" if detection_id else None,
            "image_url": f"/history/image/{detection_id}" if detection_id else None,
            "detection_id": detection_id,
            "media_type": "image"
        }
