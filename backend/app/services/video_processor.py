import cv2
import numpy as np
from ultralytics import YOLO
from . import detection_logic  # Import from our new logic file

# Tuning constants for CPU performance optimization
TARGET_FPS = 3   # process ~3 frames per second for CPU efficiency
YOLO_IMGSZ = 416 # smaller resolution for faster CPU inference (does not change output video resolution)
# Per request: detect all objects irrespective of probability -> very low confidence threshold
YOLO_CONF = 0.3
YOLO_IOU = 0.6
YOLO_MAX_DET = 100

# Color scheme for bounding boxes (BGR format for OpenCV)
COLORS = {
    'Person': (0, 255, 0),       # Green
    'Car': (255, 0, 0),          # Blue
    'Bus': (255, 0, 0),          # Blue
    'Truck': (255, 0, 0),        # Blue
    'Motorcycle': (255, 0, 0),   # Blue
    'Bicycle': (0, 255, 255),    # Yellow
    'Green Light': (0, 255, 0),  # Green
    'Red Light': (0, 0, 255),    # Red
    'Yellow Light': (0, 255, 255), # Yellow
    'Zebra Crossing': (255, 255, 0), # Cyan
    'default': (255, 255, 255)   # White
}

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
    cap = None
    frame_count = 0
    processed_frames = 0
    try:
        cap = cv2.VideoCapture(video_path)
        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return ["Error: Could not open video file."]

        # compute sampling interval
        sample_interval = max(1, int(round(fps / TARGET_FPS)))
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            # frame sampling to reduce load
            if frame_count % sample_interval != 0:
                frame_count += 1
                continue
            
            detections = []
            
            # ========== STEP 1: Run YOLOv8m (General Objects) ==========
            # Exclude class 9 (traffic lights) as we have a specialist model for that
            yolo_classes_to_keep = [i for i in range(80) if i != 9]
            results_yolo = model_yolo(
                frame,
                classes=yolo_classes_to_keep,
                conf=YOLO_CONF,
                iou=YOLO_IOU,
                imgsz=YOLO_IMGSZ,
                max_det=YOLO_MAX_DET,
                verbose=False,
                device='cpu'  # Force CPU usage
            )
            
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
            results_lights = model_lights(
                frame,
                classes=light_classes_to_keep,
                conf=YOLO_CONF,
                iou=YOLO_IOU,
                imgsz=YOLO_IMGSZ,
                max_det=YOLO_MAX_DET,
                verbose=False,
                device='cpu'  # Force CPU usage
            )
            
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
            results_zebra = model_zebra(
                frame,
                classes=zebra_classes_to_keep,
                conf=YOLO_CONF,
                iou=YOLO_IOU,
                imgsz=YOLO_IMGSZ,
                max_det=YOLO_MAX_DET,
                verbose=False,
                device='cpu'  # Force CPU usage
            )
            
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
            processed_frames += 1
            frame_count += 1

            # Optional: stop early if we already have enough guidance messages
            if len(audio_log) >= 12:
                break

    except Exception as e:
        print(f"Error during video processing: {e}")
        audio_log.append(f"An error occurred during processing: {e}")
    finally:
        try:
            if cap is not None:
                cap.release()
        except Exception:
            pass
    print(f"Processed {processed_frames} frames (sampled from {frame_count}). Found {len(audio_log)} audio messages.")
    
    return audio_log


def run_detection_with_video(video_path: str, output_video_path: str, model_yolo: YOLO, model_lights: YOLO, model_zebra: YOLO, on_progress=None) -> list[str]:
    """
    Processes a video file and creates an annotated output video with bounding boxes.
    Returns the same audio descriptions as run_detection().
    
    Args:
        video_path: Path to input video
        output_video_path: Path where annotated video will be saved
        model_yolo: YOLOv8m model for general objects
        model_lights: Traffic lights detection model
        model_zebra: Zebra crossing detection model
    
    Returns:
        List of audio description strings
    """
    audio_log = []
    detection_state = {}
    cap = None
    out = None
    frame_count = 0
    processed_frames = 0
    
    try:
        cap = cv2.VideoCapture(video_path)
        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return ["Error: Could not open video file."]

        # Setup video writer for output at ORIGINAL resolution (do not change user video resolution)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_w, frame_h))

        print(f"Creating annotated video: {output_video_path}")
        print(f"Input: {frame_w}x{frame_h}, Output: {frame_w}x{frame_h}, Total frames: {total_frames}")

        # Calculate frame skip for CPU optimization - only process every Nth frame
        frame_skip = max(1, int(round(fps / TARGET_FPS)))
        # Dynamic styling for clear, visible boxes and labels
        box_thickness = max(3, int(round(min(frame_w, frame_h) / 200)))
        font_scale = max(0.6, min(1.5, box_thickness / 4.5))
        text_thickness = max(1, box_thickness // 2)
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Only run detection on sampled frames for CPU efficiency
            should_process = (frame_count % frame_skip == 0)
            
            if should_process:
                # Make a copy for drawing
                annotated_frame = frame.copy()
                detections = []
                
                # ========== STEP 1: Run YOLOv8m (General Objects) ==========
                yolo_classes_to_keep = [i for i in range(80) if i != 9]
                results_yolo = model_yolo(
                    frame,
                    classes=yolo_classes_to_keep,
                    conf=YOLO_CONF,
                    iou=YOLO_IOU,
                    imgsz=YOLO_IMGSZ,
                    max_det=YOLO_MAX_DET,
                    verbose=False,
                    device='cpu'  # Force CPU usage
                )
                
                for r in results_yolo:
                    for box in r.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = float(box.conf[0])
                        cls_id = int(box.cls[0])
                        
                        label = detection_logic.YOLO_CLASS_NAMES.get(cls_id, f"Object_{cls_id}")
                        
                        cx = (x1 + x2) / 2
                        cy = (y1 + y2) / 2
                        
                        horiz, depth = detection_logic.get_position(cx, cy, y2, frame_w, frame_h)
                        dist_score = detection_logic.calculate_distance_score(y2, frame_h)
                        
                        detections.append({
                            'label': label, 'conf': conf,
                            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                            'cx': cx, 'cy': cy,
                            'horiz': horiz, 'depth': depth, 'dist_score': dist_score,
                            'model': 'yolo'
                        })
            
                # ========== STEP 2: Run Traffic Lights Model ==========
                light_classes_to_keep = [2, 3, 4]
                results_lights = model_lights(
                    frame,
                    classes=light_classes_to_keep,
                    conf=YOLO_CONF,
                    iou=YOLO_IOU,
                    imgsz=YOLO_IMGSZ,
                    max_det=YOLO_MAX_DET,
                    verbose=False,
                    device='cpu'  # Force CPU usage
                )
                
                for r in results_lights:
                    for box in r.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = float(box.conf[0])
                        cls_id = int(box.cls[0])
                        
                        label = detection_logic.TRAFFIC_LIGHT_CLASS_NAMES.get(cls_id, f"Light_{cls_id}")
                        
                        cx = (x1 + x2) / 2
                        cy = (y1 + y2) / 2
                        
                        horiz, depth = detection_logic.get_position(cx, cy, y2, frame_w, frame_h)
                        dist_score = detection_logic.calculate_distance_score(y2, frame_h)
                        
                        detections.append({
                            'label': label, 'conf': conf,
                            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                            'cx': cx, 'cy': cy,
                            'horiz': horiz, 'depth': depth, 'dist_score': dist_score,
                            'model': 'lights'
                        })
            
                # ========== STEP 3: Run Zebra Crossing Model ==========
                zebra_classes_to_keep = [8]
                results_zebra = model_zebra(
                    frame,
                    classes=zebra_classes_to_keep,
                    conf=YOLO_CONF,
                    iou=YOLO_IOU,
                    imgsz=YOLO_IMGSZ,
                    max_det=YOLO_MAX_DET,
                    verbose=False,
                    device='cpu'  # Force CPU usage
                )
                
                for r in results_zebra:
                    for box in r.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = float(box.conf[0])
                        cls_id = int(box.cls[0])
                        
                        label = detection_logic.ZEBRA_CLASS_NAMES.get(cls_id, f"Crossing_{cls_id}")
                        
                        cx = (x1 + x2) / 2
                        cy = (y1 + y2) / 2
                        
                        horiz, depth = detection_logic.get_position(cx, cy, y2, frame_w, frame_h)
                        dist_score = detection_logic.calculate_distance_score(y2, frame_h)
                        
                        detections.append({
                            'label': label, 'conf': conf,
                            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                            'cx': cx, 'cy': cy,
                            'horiz': horiz, 'depth': depth, 'dist_score': dist_score,
                            'model': 'zebra'
                        })
            
                # ========== STEP 4: Draw Bounding Boxes ==========
                for det in detections:
                    x1, y1, x2, y2 = int(det['x1']), int(det['y1']), int(det['x2']), int(det['y2'])
                    label = det['label']
                    conf = det['conf']
                    
                    # Get color for this object type
                    color = COLORS.get(label, COLORS['default'])
                    
                    # Draw bounding box with increased thickness for clarity
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, box_thickness)
                    
                    # Draw label background
                    label_text = f"{label} {conf:.2f}"
                    (text_w, text_h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_thickness)
                    cv2.rectangle(annotated_frame, (x1, max(0, y1 - text_h - 8)), (x1 + text_w + 6, y1), color, -1)
                    
                    # Draw label text
                    cv2.putText(annotated_frame, label_text, (x1 + 3, max(12, y1 - 4)),
                               cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), text_thickness)
                
                # ========== STEP 5: Generate Audio Messages ==========
                grouped = detection_logic.group_detections(detections, frame_w, frame_h)
                if detections:
                    audio_message = detection_logic.generate_audio_message(grouped, frame_count, fps, detection_state)
                    if audio_message:
                        audio_log.append(audio_message)
                processed_frames += 1
                
                # Write annotated frame to output video
                out.write(annotated_frame)
            else:
                # For skipped frames, just write the original frame
                out.write(frame)
            
            frame_count += 1
            
            # Show progress every 30 frames
            if frame_count % 30 == 0:
                progress = (frame_count / max(1,total_frames)) * 100
                msg = f"Processing frame {frame_count}/{total_frames}"
                print(f"Progress: {progress:.1f}% ({frame_count}/{total_frames} frames)")
                try:
                    if callable(on_progress):
                        on_progress(progress, msg)
                except Exception:
                    pass
        
    except Exception as e:
        print(f"Error during video processing with annotation: {e}")
        audio_log.append(f"An error occurred during processing: {e}")
    finally:
        try:
            if cap is not None:
                cap.release()
            if out is not None:
                out.release()
        except Exception:
            pass
    
    print(f"Annotated video saved: {output_video_path}")
    print(f"Processed {processed_frames} sampled frames from {frame_count} total frames. Found {len(audio_log)} audio messages.")
    
    return audio_log
