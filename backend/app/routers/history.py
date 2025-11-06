import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
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


def _open_file_range(file_path: str, start: int, end: int, chunk_size: int = 1024 * 1024):
    with open(file_path, 'rb') as f:
        f.seek(start)
        bytes_to_read = end - start + 1
        while bytes_to_read > 0:
            read_length = min(chunk_size, bytes_to_read)
            data = f.read(read_length)
            if not data:
                break
            bytes_to_read -= len(data)
            yield data


@router.get("/video/{detection_id}")
def get_detection_video(detection_id: int, request: Request, db: Session = Depends(database.get_db)):
    """
    Download/stream the video file for a specific detection.
    """
    detection = db.query(models.DetectionHistory)\
                  .filter(models.DetectionHistory.id == detection_id)\
                  .first()
    
    if not detection:
        raise HTTPException(status_code=404, detail="Detection history not found")
    
    print(f"Video request for detection {detection_id}: video_path = {detection.video_path}")
    
    if not detection.video_path:
        raise HTTPException(status_code=404, detail="No video file associated with this detection")
    
    if not os.path.exists(detection.video_path):
        print(f"Video file does not exist at path: {detection.video_path}")
        raise HTTPException(status_code=404, detail=f"Video file not found at expected location")
    
    # Determine media type from file extension
    file_ext = os.path.splitext(detection.video_path)[1].lower()
    media_type_map = {
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.webm': 'video/webm',
        '.mkv': 'video/x-matroska'
    }
    media_type = media_type_map.get(file_ext, 'video/mp4')

    # Support HTTP Range requests for smooth streaming
    file_size = os.path.getsize(detection.video_path)
    range_header = request.headers.get('range') or request.headers.get('Range')
    if range_header:
        # Example: "bytes=0-" or "bytes=1000-2000"
        try:
            units, rng = range_header.split('=')
            if units.strip().lower() != 'bytes':
                raise ValueError('Invalid units')
            start_str, end_str = (rng or '').split('-')
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
            start = max(0, start)
            end = min(file_size - 1, end)
            if start > end:
                start = 0
                end = file_size - 1

            headers = {
                'Content-Range': f'bytes {start}-{end}/{file_size}',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(end - start + 1),
                'Cache-Control': 'private, max-age=86400',
            }
            return StreamingResponse(
                _open_file_range(detection.video_path, start, end),
                status_code=206,
                media_type=media_type,
                headers=headers,
            )
        except Exception as e:
            print(f"Range parse error: {e}, falling back to full file")

    # Fallback: serve entire file
    print(f"Serving video (full): {detection.video_path} as {media_type}")
    resp = FileResponse(
        detection.video_path,
        media_type=media_type,
        filename=os.path.basename(detection.video_path)
    )
    resp.headers['Accept-Ranges'] = 'bytes'
    resp.headers['Cache-Control'] = 'private, max-age=86400'
    return resp


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
