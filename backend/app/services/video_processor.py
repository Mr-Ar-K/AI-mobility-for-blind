import cv2
from ultralytics import YOLO
from . import detection_logic  # Import from our new logic file

def run_detection(video_path: str, model: YOLO) -> list[str]:
    """
    Processes a video file and returns a list of audio descriptions.
    This is adapted from the MAIN PROCESSING loop in Context 2.
    """
    
    # These are reset for every video processed
    audio_log = []
    detection_state = {}

    try:
        cap = cv2.VideoCapture(video_path)
        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return ["Error: Could not open video file."]

        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run YOLO detection
            results = model(frame, verbose=False)
            
            detections = []
            
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    label = detection_logic.CLASS_NAMES.get(cls_id, f"Class_{cls_id}")
                    
                    cx = (x1 + x2) / 2
                    cy = (y1 + y2) / 2
                    
                    horiz, depth = detection_logic.get_position(cx, cy, y2, frame_w, frame_h)
                    dist_score = detection_logic.calculate_distance_score(y2, frame_h)
                    
                    detections.append({
                        'label': label, 'conf': conf,
                        'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                        'cx': cx, 'cy': cy,
                        'horiz': horiz, 'depth': depth, 'dist_score': dist_score
                    })
            
            # Group detections
            grouped = detection_logic.group_detections(detections, frame_w, frame_h)
            
            # Generate audio guidance
            if detections:
                # We pass detection_state so it can be modified by the function
                audio_message = detection_logic.generate_audio_message(grouped, frame_count, fps, detection_state)
                if audio_message:
                    # Log the text string
                    audio_log.append(audio_message)
            
            frame_count += 1

    except Exception as e:
        print(f"Error during video processing: {e}")
        audio_log.append(f"An error occurred during processing: {e}")
    finally:
        cap.release()
        print(f"Processed {frame_count} frames. Found {len(audio_log)} audio messages.")
    
    return audio_log
