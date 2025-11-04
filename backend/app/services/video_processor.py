import cv2
import numpy as np
import torch
from ultralytics import YOLO
import cv2
import numpy as np
try:
    import imageio
    import imageio_ffmpeg
    _HAS_IMAGEIO_FFMPEG = True
except Exception:
    _HAS_IMAGEIO_FFMPEG = False
from . import detection_logic  # Import from our new logic file

# Dynamic performance optimization based on available hardware
def get_optimal_settings():
    """Dynamically determine optimal settings based on GPU/CPU availability"""
    has_gpu = torch.cuda.is_available()
    
    if has_gpu:
        # GPU settings - more aggressive processing
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
        return {
            'TARGET_FPS': 9 if gpu_memory > 4 else 6,  # Process more frames
            'YOLO_IMGSZ': 640,  # Higher resolution for better accuracy
            'YOLO_CONF': 0.4,
            'YOLO_IOU': 0.5,
            'YOLO_MAX_DET': 150,
            'DEVICE': 'cuda'
        }
    else:
        # CPU settings - conservative for smooth performance
        cpu_count = torch.get_num_threads()
        return {
            'TARGET_FPS': 5 if cpu_count >= 8 else 4,
            'YOLO_IMGSZ': 480,  # Balanced resolution
            'YOLO_CONF': 0.45,
            'YOLO_IOU': 0.6,
            'YOLO_MAX_DET': 100,
            'DEVICE': 'cpu'
        }

# Get optimal settings
SETTINGS = get_optimal_settings()
TARGET_FPS = SETTINGS['TARGET_FPS']
YOLO_IMGSZ = SETTINGS['YOLO_IMGSZ']
YOLO_CONF = SETTINGS['YOLO_CONF']
YOLO_IOU = SETTINGS['YOLO_IOU']
YOLO_MAX_DET = SETTINGS['YOLO_MAX_DET']
DEVICE = SETTINGS['DEVICE']

print(f"🚀 Video Processor initialized with {DEVICE.upper()} - Target FPS: {TARGET_FPS}, Image Size: {YOLO_IMGSZ}")

# Color scheme for bounding boxes (BGR format for OpenCV) - Only 4 classes now
COLORS = {
    'Car': (255, 0, 0),          # Blue
    'Person': (0, 255, 0),       # Green
    'Green Light': (0, 255, 0),  # Green
    'zebra crossing': (0, 255, 255), # Yellow
    'default': (255, 255, 255)   # White
}

class _FrameWriter:
    """Unified frame writer that wraps either imageio-ffmpeg or OpenCV VideoWriter."""
    def __init__(self, writer, mode: str, frame_size: tuple[int, int], fps: float):
        self._writer = writer
        self._mode = mode  # 'imageio' or 'cv2'
        self._size = frame_size
        self._fps = fps
    def write(self, frame: np.ndarray):
        if self._mode == 'imageio':
            # Convert BGR -> RGB for imageio/ffmpeg
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self._writer.append_data(rgb)
        else:
            self._writer.write(frame)
    def release(self):
        if self._mode == 'imageio':
            try:
                self._writer.close()
            except Exception:
                pass
        else:
            try:
                self._writer.release()
            except Exception:
                pass


def _open_video_writer(output_path: str, fps: float, frame_size: tuple[int, int]):
    """Open a browser-playable MP4 writer. Prefer imageio-ffmpeg (H.264), fallback to OpenCV codecs."""
    # Prefer imageio-ffmpeg if available to produce H.264/yuv420p MP4
    if _HAS_IMAGEIO_FFMPEG and output_path.lower().endswith('.mp4'):
        try:
            writer = imageio.get_writer(
                output_path,
                fps=fps,
                codec='libx264',
                format='ffmpeg',
                output_params=[
                    '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart',
                    # Compatibility/performance tuning
                    '-preset', 'veryfast',    # speed up encoding
                    '-crf', '23',             # reasonable quality-size tradeoff
                    '-profile:v', 'baseline', # broad device compatibility
                    '-level', '3.0',
                    '-g', str(max(24, int(fps) * 2) if fps else 48),  # GOP size
                    '-bf', '0',               # disable B-frames for some players
                ],
            )
            print("Using imageio-ffmpeg (libx264) for MP4 output")
            return _FrameWriter(writer, 'imageio', frame_size, fps), 'libx264'
        except Exception as e:
            print(f"imageio-ffmpeg unavailable or failed: {e}. Falling back to OpenCV VideoWriter.")

    # Fallback to OpenCV VideoWriter with safer codecs
    codec_candidates = [
        ('mp4v', 'MPEG-4 Part 2 (mp4v)'),
        ('XVID', 'Xvid (xvid)'),
        ('MJPG', 'Motion JPEG (mjpg)')
    ]
    last_err = None
    for fourcc_name, desc in codec_candidates:
        try:
            fourcc = cv2.VideoWriter_fourcc(*fourcc_name)
            writer = cv2.VideoWriter(output_path, fourcc, fps, frame_size)
            if writer.isOpened():
                print(f"VideoWriter initialized with codec {fourcc_name} - {desc}")
                return _FrameWriter(writer, 'cv2', frame_size, fps), fourcc_name
            else:
                try:
                    writer.release()
                except Exception:
                    pass
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Failed to initialize VideoWriter for {output_path}. Last error: {last_err}")

def run_detection(video_path: str, model: YOLO) -> list[str]:
    """
    Processes a video file using single custom YOLOv8n model and returns a list of audio descriptions.
    
    Single-model detection pipeline:
    Detects 4 classes: Car, Person, Green Light, zebra crossing
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
            
            # ========== Run Single Custom YOLOv8n Model ==========
            # Detects: Car (0), Person (1), Green Light (2), zebra crossing (3)
            results = model(
                frame,
                conf=YOLO_CONF,
                iou=YOLO_IOU,
                imgsz=YOLO_IMGSZ,
                max_det=YOLO_MAX_DET,
                verbose=False,
                device=DEVICE
            )
            
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    
                    # Map class IDs to our labels
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
            
            # ========== Process Detections ==========
            # Group all detections
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


def run_detection_with_video(video_path: str, output_video_path: str, model: YOLO, on_progress=None) -> list[str]:
    """
    Processes a video file and creates an annotated output video with bounding boxes.
    Returns the same audio descriptions as run_detection().
    
    Args:
        video_path: Path to input video
        output_video_path: Path where annotated video will be saved
        model: Custom YOLOv8n model for 4 classes (Car, Person, Green Light, zebra crossing)
        on_progress: Optional callback for progress updates
    
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
        # Sanitize FPS to a sane, browser-friendly range (10..60) and use integer
        try:
            fps = int(max(10, min(60, round(float(fps) if fps else 30))))
        except Exception:
            fps = 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return ["Error: Could not open video file."]

        # Setup video writer at original resolution, but ensure even dimensions for yuv420p encoders
        out_w = frame_w - (frame_w % 2)
        out_h = frame_h - (frame_h % 2)
        if (out_w != frame_w) or (out_h != frame_h):
            print(f"Adjusting output size to even dimensions for encoder: {frame_w}x{frame_h} -> {out_w}x{out_h}")
        # Try H.264 first (via imageio-ffmpeg); fallback to other codecs.
        out, chosen_codec = _open_video_writer(output_video_path, fps, (out_w, out_h))

        print(f"Creating annotated video: {output_video_path} (codec: {chosen_codec})")
        print(f"Input: {frame_w}x{frame_h}, Output: {out_w}x{out_h}, FPS: {fps}, Total frames: {total_frames}")

        # Dynamic styling for clear, visible boxes and labels
        box_thickness = max(3, int(round(min(frame_w, frame_h) / 200)))
        font_scale = max(0.6, min(1.5, box_thickness / 4.5))
        text_thickness = max(1, box_thickness // 2)

        # Allow lower model resolution for reduced CPU load
        model_imgsz = YOLO_IMGSZ if YOLO_IMGSZ <= min(frame_w, frame_h) else min(frame_w, frame_h)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Optionally resize a COPY for lower CPU load, but keep original frame size for output
            process_frame = frame
            if min(frame_w, frame_h) > 640:
                # compute resized dimensions preserving aspect ratio
                if frame_w <= frame_h:
                    new_w = 640
                    new_h = int(round(frame_h * (640.0 / frame_w)))
                else:
                    new_h = 640
                    new_w = int(round(frame_w * (640.0 / frame_h)))
                process_frame = cv2.resize(frame, (new_w, new_h))

            annotated_frame = frame.copy()
            detections = []

            # ========== Run Single Custom YOLOv8n Model ========== 
            results = model(
                process_frame,
                conf=YOLO_CONF,
                iou=YOLO_IOU,
                imgsz=model_imgsz,
                max_det=YOLO_MAX_DET,
                verbose=False,
                device=DEVICE
            )

            # Scale factors to map detections back to original frame size
            scale_x = frame_w / process_frame.shape[1]
            scale_y = frame_h / process_frame.shape[0]

            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    # Map coords back to original frame size
                    x1 *= scale_x; x2 *= scale_x
                    y1 *= scale_y; y2 *= scale_y
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
                        'horiz': horiz, 'depth': depth, 'dist_score': dist_score
                    })

            # ========== Draw Bounding Boxes ========== 
            for det in detections:
                x1, y1, x2, y2 = int(det['x1']), int(det['y1']), int(det['x2']), int(det['y2'])
                label = det['label']
                conf = det['conf']

                color = COLORS.get(label, COLORS['default'])
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, box_thickness)
                label_text = f"{label} {conf:.2f}"
                (text_w, text_h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_thickness)
                cv2.rectangle(annotated_frame, (x1, max(0, y1 - text_h - 8)), (x1 + text_w + 6, y1), color, -1)
                cv2.putText(annotated_frame, label_text, (x1 + 3, max(12, y1 - 4)),
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), text_thickness)

            grouped = detection_logic.group_detections(detections, frame_w, frame_h)
            if detections:
                audio_message = detection_logic.generate_audio_message(grouped, frame_count, fps, detection_state)
                if audio_message:
                    audio_log.append(audio_message)
            processed_frames += 1
            # Crop to even writer size if needed (encoder requirement)
            if annotated_frame.shape[1] != out_w or annotated_frame.shape[0] != out_h:
                annotated_frame = annotated_frame[0:out_h, 0:out_w]
            out.write(annotated_frame)
            frame_count += 1
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
