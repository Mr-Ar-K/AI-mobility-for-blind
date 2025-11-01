import numpy as np
from collections import defaultdict
from ultralytics import YOLO

# ================================================================
# CONFIGURATION - Multi-Model Detection System
# ================================================================
FRAME_GROUPING_WINDOW = 120
CONFIDENCE_THRESHOLD = 0.7

# YOLOv8m standard COCO class names (we use cars, people, etc.)
# Full COCO classes: https://github.com/ultralytics/ultralytics/blob/main/ultralytics/cfg/datasets/coco.yaml
YOLO_CLASS_NAMES = {
    0: "Person",
    1: "Bicycle",
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck",
    # Add more as needed, but we exclude class 9 (traffic light) in video_processor
}

# Traffic Lights Model - Classes 2, 3, 4 correspond to light colors
TRAFFIC_LIGHT_CLASS_NAMES = {
    2: "Green Light",
    3: "Red Light",
    4: "Yellow Light"
}

# Zebra Crossing Model - Class 8 is zebra crossing
ZEBRA_CLASS_NAMES = {
    8: "Zebra Crossing"
}

# Categories for detection logic
VEHICLE_CLASSES = ["Car", "Bus", "Truck", "Motorcycle", "Bicycle"]
TRAFFIC_LIGHTS = ["Green Light", "Red Light", "Yellow Light"]
ZEBRA_CROSSING = ["Zebra Crossing"]

# ================================================================
# HELPER FUNCTIONS (Copied from Context 2)
# ================================================================

def calculate_distance_score(y2, frame_h):
    """Calculate priority based on distance (higher y2 = nearer)"""
    return y2 / frame_h

def get_position(cx, cy, y2, frame_w, frame_h):
    """Determine horizontal and depth position"""
    # Horizontal position
    if cx < frame_w / 3:
        horiz = "left"
    elif cx > (2 * frame_w) / 3:
        horiz = "right"
    else:
        horiz = "center"
    
    # Depth/Distance
    if y2 > frame_h * 0.75:
        depth = "very close"
    elif y2 > frame_h * 0.5:
        depth = "approaching"
    else:
        depth = "far"
    
    return horiz, depth

def group_detections(detections, frame_w, frame_h):
    """Group similar detections to avoid redundancy"""
    grouped = defaultdict(list)
    for det in detections:
        label = det['label']
        horiz = det['horiz']
        depth = det['depth']
        key = f"{label}_{horiz}_{depth}"
        grouped[key].append(det)
    return grouped

def should_announce(detection_key, current_frame, detection_state):
    """Check if we should announce this detection based on frame grouping"""
    if detection_key not in detection_state:
        detection_state[detection_key] = {
            'first_frame': current_frame,
            'last_frame': current_frame,
            'last_announced': current_frame,
            'count': 1
        }
        return True
    else:
        state = detection_state[detection_key]
        state['last_frame'] = current_frame
        state['count'] += 1
        
        frames_since_announcement = current_frame - state['last_announced']
        if frames_since_announcement >= FRAME_GROUPING_WINDOW:
            state['last_announced'] = current_frame
            return True
        return False

def generate_audio_message(grouped_detections, frame_count, fps, detection_state):
    """Generate human-like audio guidance - ONE PRIORITY MESSAGE ONLY"""
    messages = []
    priority_scores = []
    
    # Check for traffic lights first (highest priority)
    for key, dets in grouped_detections.items():
        if any(light in key for light in TRAFFIC_LIGHTS):
            det = dets[0]
            if det['conf'] < CONFIDENCE_THRESHOLD:
                continue
            if not should_announce(key, frame_count, detection_state):
                continue
            
            # Handle different traffic light colors
            if "Green Light" in det['label']:
                msg = "Green light ahead. It's safe to cross."
                messages.append(msg)
                priority_scores.append(9)
            elif "Red Light" in det['label']:
                msg = "Red light ahead. Stop and wait."
                messages.append(msg)
                priority_scores.append(10)  # Red light is highest priority
            elif "Yellow Light" in det['label']:
                msg = "Yellow light ahead. Prepare to stop."
                messages.append(msg)
                priority_scores.append(9)
    
    # Check for zebra crossing
    zebra_detected = False
    zebra_key = None
    for key, dets in grouped_detections.items():
        label = dets[0]['label']
        if label in ZEBRA_CROSSING:
            if dets[0]['conf'] >= CONFIDENCE_THRESHOLD:
                zebra_detected = True
                zebra_key = key
            break
    
    # Check for vehicles and people
    vehicles_left = []
    vehicles_right = []
    vehicles_center = []
    people_detected = []
    
    for key, dets in grouped_detections.items():
        det = dets[0]
        label = det['label']
        horiz = det['horiz']
        depth = det['depth']
        dist_score = det['dist_score']
        count = len(dets)
        
        if det['conf'] < CONFIDENCE_THRESHOLD:
            continue
        
        if label in VEHICLE_CLASSES:
            vehicle_info = {
                'label': label,
                'horiz': horiz,
                'depth': depth,
                'dist_score': dist_score,
                'count': count,
                'key': key
            }
            
            if horiz == "left":
                vehicles_left.append(vehicle_info)
            elif horiz == "right":
                vehicles_right.append(vehicle_info)
            else:
                vehicles_center.append(vehicle_info)
        
        elif label == "Person":
            people_detected.append({
                'horiz': horiz,
                'depth': depth,
                'dist_score': dist_score,
                'count': count,
                'key': key
            })
    
    # Sort vehicles by distance (closest first)
    vehicles_left.sort(key=lambda x: x['dist_score'], reverse=True)
    vehicles_right.sort(key=lambda x: x['dist_score'], reverse=True)
    vehicles_center.sort(key=lambda x: x['dist_score'], reverse=True)
    
    # Generate vehicle warnings - CENTER (front)
    if vehicles_center:
        v = vehicles_center[0]
        
        if should_announce(v['key'], frame_count, detection_state):
            count_str = f"{v['count']} " if v['count'] > 1 else "A "
            vehicle_name = f"{v['label']}s" if v['count'] > 1 else v['label']
            
            if v['dist_score'] > 0.75:
                msg = f"Watch out! {count_str}{vehicle_name} right in front of you! Stay where you are!"
                priority = 10
            elif v['dist_score'] > 0.5:
                msg = f"Careful! {count_str}{vehicle_name} coming towards you."
                priority = 8
            else:
                # Skip far vehicles to reduce audio
                msg = None
                priority = 0
            
            if msg:
                messages.append(msg)
                priority_scores.append(priority)
    
    # LEFT side
    if vehicles_left:
        v = vehicles_left[0]
        
        if should_announce(v['key'], frame_count, detection_state):
            count_str = f"{v['count']} " if v['count'] > 1 else "A "
            vehicle_name = f"{v['label']}s" if v['count'] > 1 else v['label']
            
            if v['dist_score'] > 0.75:
                msg = f"Warning! {count_str}{vehicle_name} on your left side! Don't move!"
                priority = 9
            elif v['dist_score'] > 0.5:
                msg = f"{count_str}{vehicle_name} approaching on your left."
                priority = 7
            else:
                # Skip far vehicles
                msg = None
                priority = 0
            
            if msg:
                messages.append(msg)
                priority_scores.append(priority)
    
    # RIGHT side
    if vehicles_right:
        v = vehicles_right[0]
        
        if should_announce(v['key'], frame_count, detection_state):
            count_str = f"{v['count']} " if v['count'] > 1 else "A "
            vehicle_name = f"{v['label']}s" if v['count'] > 1 else v['label']
            
            if v['dist_score'] > 0.75:
                msg = f"Warning! {count_str}{vehicle_name} on your right side! Don't move!"
                priority = 9
            elif v['dist_score'] > 0.5:
                msg = f"{count_str}{vehicle_name} approaching on your right."
                priority = 7
            else:
                # Skip far vehicles
                msg = None
                priority = 0
            
            if msg:
                messages.append(msg)
                priority_scores.append(priority)
    
    # Zebra crossing guidance
    if zebra_detected and zebra_key:
        if should_announce(zebra_key, frame_count, detection_state):
            if not vehicles_center and not vehicles_left and not vehicles_right:
                msg = "Zebra crossing in front of you. No vehicles nearby. You can cross now."
                messages.append(msg)
                priority_scores.append(7)
            elif vehicles_center or vehicles_left or vehicles_right:
                has_close_vehicle = any(v['dist_score'] > 0.6 for v in vehicles_center + vehicles_left + vehicles_right)
                if has_close_vehicle:
                    msg = "Zebra crossing ahead, but vehicles are nearby. Wait for them to pass."
                    messages.append(msg)
                    priority_scores.append(8)
    
    # People detection - only announce if very close
    if people_detected:
        people_detected.sort(key=lambda x: x['dist_score'], reverse=True)
        p = people_detected[0]
        
        # Only announce people if they are very close (reduce audio)
        if p['dist_score'] > 0.75:
            if should_announce(p['key'], frame_count, detection_state):
                count_str = f"{p['count']} people" if p['count'] > 1 else "Person"
                
                # Human-like directional guidance
                if p['horiz'] == "center":
                    position = "ahead"
                elif p['horiz'] == "left":
                    position = "left"
                else:
                    position = "right"
                
                msg = f"{count_str} {position}."
                messages.append(msg)
                priority_scores.append(4)
    
    # Return ONLY the highest priority message (keeps audio concise)
    if messages:
        sorted_msgs = sorted(zip(priority_scores, messages), key=lambda x: x[0], reverse=True)
        return sorted_msgs[0][1]  # Return only top priority message
    
    return None
