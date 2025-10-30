import cv2
from ultralytics import YOLO
from . import detection_logic  # Import from our new logic file

def run_detection(video_path: str, model_yolo: YOLO, model_lights: YOLO, model_zebra: YOLO) -> list[str]:
    """
    Processes a video file using three models in sequence and returns a list of audio descriptions.
    
    Multi-model detection pipeline:
    1. YOLOv8m: Detects general objects (vehicles, people, etc.) - excluding traffic lights (class 9)
    2. Traffic Lights Model: Detects traffic light colors (green=2, red=3, yellow=4)
    3. Zebra Crossing Model: Detects zebra crossings (class 8)
    
    All detections are merged and processed together for comprehensive scene understanding.
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
            
            detections = []
            
            # ========== STEP 1: Run YOLOv8m (General Objects) ==========
            # Exclude class 9 (traffic lights) as we have a specialist model for that
            yolo_classes_to_keep = [i for i in range(80) if i != 9]
            results_yolo = model_yolo(frame, classes=yolo_classes_to_keep, conf=0.4, verbose=False)
            
            for r in results_yolo:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    
                    # Map YOLO class IDs to our labels
                    label = detection_logic.YOLO_CLASS_NAMES.get(cls_id, f"Object_{cls_id}")
                    
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
            
            # ========== STEP 2: Run Traffic Lights Model ==========
            # Only keep classes 2, 3, 4 (green, red, yellow)
            light_classes_to_keep = [2, 3, 4]
            results_lights = model_lights(frame, classes=light_classes_to_keep, conf=0.4, verbose=False)
            
            for r in results_lights:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    
                    # Map traffic light class IDs
                    label = detection_logic.TRAFFIC_LIGHT_CLASS_NAMES.get(cls_id, f"Light_{cls_id}")
                    
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
            
            # ========== STEP 3: Run Zebra Crossing Model ==========
            # Only keep class 8 (zebra crossing)
            zebra_classes_to_keep = [8]
            results_zebra = model_zebra(frame, classes=zebra_classes_to_keep, conf=0.4, verbose=False)
            
            for r in results_zebra:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    
                    # Map zebra crossing class ID
                    label = detection_logic.ZEBRA_CLASS_NAMES.get(cls_id, f"Crossing_{cls_id}")
                    
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
            
            # ========== STEP 4: Process Merged Detections ==========
            # Group all detections from all three models
            grouped = detection_logic.group_detections(detections, frame_w, frame_h)
            
            # Generate audio guidance based on all detections
            if detections:
                audio_message = detection_logic.generate_audio_message(grouped, frame_count, fps, detection_state)
                if audio_message:
                    audio_log.append(audio_message)
            
            frame_count += 1

    except Exception as e:
        print(f"Error during video processing: {e}")
        audio_log.append(f"An error occurred during processing: {e}")
    finally:
        cap.release()
        print(f"Processed {frame_count} frames. Found {len(audio_log)} audio messages.")
    
    return audio_log
