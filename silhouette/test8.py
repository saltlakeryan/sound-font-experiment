import os
import cv2
import numpy as np
import mediapipe as mp
from ultralytics import YOLO

# 1. Load YOLO for robust multi-person localization
yolo_model = YOLO("yolo11m-pose.pt")

# Initialize MediaPipe Pose Engine
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.4)

input_folder = "input_images/"
output_folder = "output_hybrid_skeletons/"
os.makedirs(output_folder, exist_ok=True)

# Connection maps
BODY_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), # Arms & Shoulders
    (11, 23), (12, 24), (23, 24),                    # Torso
    (23, 25), (25, 27), (24, 26), (26, 28)           # Legs
]
FOOT_CONNECTIONS = [
    (27, 29), (29, 31), (27, 31), # Left Foot
    (28, 30), (30, 32), (28, 32)  # Right Foot
]

image_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.png')]
print(f"Processing {len(image_files)} files with multi-person hybrid tracking...")

for filename in sorted(image_files):
    img_path = os.path.join(input_folder, filename)
    image = cv2.imread(img_path)
    if image is None: continue
    
    h, w, _ = image.shape
    skeleton_canvas = np.zeros((h, w, 3), dtype=np.uint8)
    
    # 2. Let YOLO find ALL people in the scene first
    yolo_results = yolo_model.predict(img_path, imgsz=1280, verbose=False)[0]
    
    if yolo_results.boxes is not None:
        boxes = yolo_results.boxes.xyxy.cpu().numpy()
        
        # Unique color cycle per person
        for dancer_idx, box in enumerate(boxes):
            if int(yolo_results.boxes.cls[dancer_idx]) != 0: continue # Only process humans
            
            # Extract bounding box with padding
            x1, y1, x2, y2 = map(int, box)
            pad = 20
            x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
            x2, y2 = min(w, x2 + pad), min(h, y2 + pad)
            
            crop = image[y1:y2, x1:x2]
            if crop.size == 0: continue
            
            # 3. Pass individual cropped dancer to MediaPipe
            crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            mp_results = pose.process(crop_rgb)
            
            if mp_results.pose_landmarks:
                ch, cw, _ = crop.shape
                landmarks = mp_results.pose_landmarks.landmark
                
                # Dynamic random color for this specific person
                color = list(np.random.randint(80, 256, size=3, dtype=int))
                bgr_color = [int(c) for c in color]
                
                # Convert crop relative landmarks back to global image coordinates
                coords = {}
                for idx, lm in enumerate(landmarks):
                    if lm.visibility > 0.4:
                        global_x = x1 + int(lm.x * cw)
                        global_y = y1 + int(lm.y * ch)
                        coords[idx] = (global_x, global_y)
                    else:
                        coords[idx] = None

                # Draw body framework bones
                for start, end in BODY_CONNECTIONS:
                    if coords[start] and coords[end]:
                        cv2.line(skeleton_canvas, coords[start], coords[end], bgr_color, 4, cv2.LINE_AA)

                # Draw explicit native foot shapes (Toe tracking included)
                for start, end in FOOT_CONNECTIONS:
                    if coords[start] and coords[end]:
                        cv2.line(skeleton_canvas, coords[start], coords[end], (255, 255, 255), 3, cv2.LINE_AA)

                # Overlay node joints
                for idx, pt in coords.items():
                    if pt:
                        cv2.circle(skeleton_canvas, pt, 5, (255, 255, 255), -1, cv2.LINE_AA)
                        cv2.circle(skeleton_canvas, pt, 5, bgr_color, 2, cv2.LINE_AA)

        # Save individual frame files instantly
        output_path = os.path.join(output_folder, filename)
        cv2.imwrite(output_path, skeleton_canvas)
        print(f" Saved multi-person map: {output_path}")
    else:
        print(f" Skipped {filename} (Zero objects captured).")

pose.close()
print("\nHybrid multi-person framework complete!")
