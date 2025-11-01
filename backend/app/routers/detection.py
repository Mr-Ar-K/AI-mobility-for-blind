import os
import shutil
import uuid
import time
from datetime import datetime
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from ultralytics import YOLO
from starlette.concurrency import run_in_threadpool

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

# Progress tracking storage (in-memory for simplicity)
# Format: {task_id: {"status": "processing", "progress": 45, "message": "Processing frame 100/200", "estimated_time": 30}}
progress_store = {}

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

@router.get("/test-models")
async def test_models(request: Request):
    """Test endpoint to verify all models are loaded correctly"""
    try:
        model_yolo = request.app.state.model_yolo
        model_lights = request.app.state.model_lights
        model_zebra = request.app.state.model_zebra
        
        return {
            "status": "success",
            "models_loaded": {
                "yolov8m": str(type(model_yolo)),
                "traffic_lights": str(type(model_lights)),
                "zebra_crossing": str(type(model_zebra))
            },
            "message": "All models are loaded and ready"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Model loading error: {str(e)}"
        }

@router.get("/progress/{task_id}")
async def get_progress(task_id: str):
    """
    Get the progress of a detection task.
    Returns status, progress percentage, message, and estimated time remaining.
    """
    if task_id not in progress_store:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return progress_store[task_id]

@router.post("/{user_id}")
async def detect_video(
    user_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    lang: Optional[str] = 'en'
):
    # Get all three models from app state
    model_yolo = request.app.state.model_yolo
    model_lights = request.app.state.model_lights
    model_zebra = request.app.state.model_zebra
    
    # Generate task ID for progress tracking
    task_id = str(uuid.uuid4())
    progress_store[task_id] = {
        "status": "uploading",
        "progress": 0,
        "message": "Uploading video...",
        "estimated_time": None
    }
    
    # 1. Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Save video to a temporary file
    # Create a unique filename to avoid conflicts
    file_extension = os.path.splitext(file.filename)[1]
    temp_filename = f"{uuid.uuid4()}{file_extension}"
    temp_video_path = os.path.join(TEMP_UPLOAD_DIR, temp_filename)
    
    start_time = time.time()
    
    try:
        with open(temp_video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        upload_time = time.time() - start_time
        print(f"Video uploaded in {upload_time:.2f} seconds")
        progress_store[task_id] = {
            "status": "uploaded",
            "progress": 10,
            "message": "Video uploaded successfully",
            "estimated_time": None
        }
    except Exception as e:
        progress_store[task_id] = {"status": "failed", "progress": 0, "message": f"Upload failed: {e}", "estimated_time": None}
        raise HTTPException(status_code=500, detail=f"Failed to save video file: {e}")
    finally:
        file.file.close()

    # 3. Get timestamp and create user storage directory
    detection_timestamp = datetime.now()
    user_storage_dir = get_user_storage_path(user.username, detection_timestamp)
    
    # 3.5. Define output video path (annotated version)
    video_filename = f"video_{detection_timestamp.strftime('%H-%M-%S')}{file_extension}"
    saved_video_path = os.path.join(user_storage_dir, video_filename)
    
    # 4. Process the video with all three models and create annotated video
    print(f"Starting video detection processing...")
    progress_store[task_id] = {
        "status": "processing",
        "progress": 20,
        "message": "Detecting objects in video...",
        "estimated_time": None
    }
    
    detection_start = time.time()
    try:
        # Limit concurrent processing to avoid CPU overload
        async with request.app.state.semaphore:
            # Progress callback to update frontend more frequently
            def report_progress(pct: float, message: str = None):
                progress_store[task_id] = {
                    "status": "processing",
                    "progress": max(0, min(100, int(pct))),
                    "message": message or "Processing video...",
                    "estimated_time": None
                }

            audio_results_list = await run_in_threadpool(
                video_processor.run_detection_with_video,
                temp_video_path,
                saved_video_path,
                model_yolo,
                model_lights,
                model_zebra,
                report_progress
            )
        detection_time = time.time() - detection_start
        print(f"Detection completed in {detection_time:.2f} seconds")
        
        progress_store[task_id] = {
            "status": "processing",
            "progress": 70,
            "message": "Detection complete, generating audio...",
            "estimated_time": None
        }
        
        # DELETE UPLOADED VIDEO IMMEDIATELY AFTER PROCESSING
        try:
            os.remove(temp_video_path)
            print(f"Deleted uploaded video: {temp_video_path}")
        except Exception as e:
            print(f"Warning: Failed to delete uploaded file {temp_video_path}: {e}")
            
    except Exception as e:
        # Clean up on error
        progress_store[task_id] = {"status": "failed", "progress": 0, "message": f"Detection failed: {e}", "estimated_time": None}
        try:
            os.remove(temp_video_path)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Failed during video processing: {e}")
    
    # 5. Generate audio file and save to user's directory
    saved_audio_path = None
    audio_start = time.time()
    try:
        # Speed up audio generation with shorter pauses
        generator = audio_generator.AudioGenerator(language=lang or 'en', pause_duration=250)
        temp_audio_path = generator.generate_audio_quick(audio_results_list)
        
        # Move audio to permanent storage
        audio_filename = f"audio_{detection_timestamp.strftime('%H-%M-%S')}.mp3"
        saved_audio_path = os.path.join(user_storage_dir, audio_filename)
        shutil.move(temp_audio_path, saved_audio_path)
        audio_time = time.time() - audio_start
        print(f"Audio generated and saved in {audio_time:.2f} seconds: {saved_audio_path}")
    except Exception as e:
        print(f"Warning: Failed to generate/save audio: {e}")
        # Continue even if audio generation fails

    # 6. Save results to history (including video and audio paths)
    try:
        history_entry = models.DetectionHistory(
            user_id=user_id,
            results=audio_results_list,
            video_path=saved_video_path,
            audio_path=saved_audio_path,
            media_type="video"
        )
        db.add(history_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to save history: {e}")
        # We don't raise an error here, as the user should still get their results

    # 7. Return the audio strings and timing information
    total_time = time.time() - start_time
    print(f"Total processing time: {total_time:.2f} seconds")
    
    progress_store[task_id] = {
        "status": "completed",
        "progress": 100,
        "message": f"Processing complete in {total_time:.1f} seconds",
        "estimated_time": 0,
        "total_time": total_time
    }
    
    return {
        "task_id": task_id,
        "results": audio_results_list,
        "processing_time": round(total_time, 2),
        "message": "Detection completed successfully"
    }


@router.post("/{user_id}/with-audio", response_model=Dict)
async def detect_video_with_audio(
    user_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    lang: Optional[str] = 'en'
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
    
    start_time = time.time()

    try:
        with open(temp_video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        upload_time = time.time() - start_time
        print(f"Video uploaded in {upload_time:.2f} seconds")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video file: {e}")
    finally:
        file.file.close()

    # 3. Get timestamp and create user storage directory first
    detection_timestamp = datetime.now()
    user_storage_dir = get_user_storage_path(user.username, detection_timestamp)
    
    # 4. Define output video path for annotated video
    video_filename = f"video_{detection_timestamp.strftime('%H-%M-%S')}{file_extension}"
    saved_video_path = os.path.join(user_storage_dir, video_filename)
    
    # 5. Process the video with all three models and save with bounding boxes
    print(f"Starting video detection processing...")
    detection_start = time.time()
    try:
        async with request.app.state.semaphore:
            audio_results_list = await run_in_threadpool(
                video_processor.run_detection_with_video,
                temp_video_path,
                saved_video_path,  # Save annotated video directly
                model_yolo,
                model_lights,
                model_zebra,
                None
            )
        detection_time = time.time() - detection_start
        print(f"Detection completed in {detection_time:.2f} seconds")
        print(f"Annotated video saved to: {saved_video_path}")
        
        # DELETE UPLOADED VIDEO IMMEDIATELY AFTER PROCESSING
        try:
            os.remove(temp_video_path)
            print(f"Deleted uploaded video: {temp_video_path}")
        except Exception as e:
            print(f"Warning: Failed to delete uploaded file {temp_video_path}: {e}")
            
    except Exception as e:
        # Clean up on error
        try:
            os.remove(temp_video_path)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Failed during video processing: {e}")
    
    # 6. Generate audio file and save to user's directory
    saved_audio_path = None
    audio_start = time.time()
    try:
        generator = audio_generator.AudioGenerator(language=lang or 'en', pause_duration=250)
        temp_audio_path = generator.generate_audio_quick(audio_results_list)
        
        # Move audio to permanent storage
        audio_filename = f"audio_{detection_timestamp.strftime('%H-%M-%S')}.mp3"
        saved_audio_path = os.path.join(user_storage_dir, audio_filename)
        shutil.move(temp_audio_path, saved_audio_path)
        audio_time = time.time() - audio_start
        print(f"Audio generated and saved in {audio_time:.2f} seconds: {saved_audio_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {e}")

    # 7. Save results to history (video is already saved with annotations)
    try:
        history_entry = models.DetectionHistory(
            user_id=user_id,
            results=audio_results_list,
            video_path=saved_video_path,
            audio_path=saved_audio_path,
            media_type="video"
        )
        db.add(history_entry)
        db.commit()
        db.refresh(history_entry)
        detection_id = history_entry.id
    except Exception as e:
        db.rollback()
        print(f"Failed to save history: {e}")
        detection_id = None

    # 8. Calculate total time and return
    total_time = time.time() - start_time
    print(f"Total processing time: {total_time:.2f} seconds")
    
    return {
        "text_results": audio_results_list,
        "audio_file": os.path.basename(saved_audio_path) if saved_audio_path else None,
        "audio_url": f"/history/audio/{detection_id}" if detection_id else None,
        "video_url": f"/history/video/{detection_id}" if detection_id else None,
        "detection_id": detection_id,
        "processing_time": round(total_time, 2),
        "message": "Detection completed successfully"
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
