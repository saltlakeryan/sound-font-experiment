import os
import math
import cv2
import numpy as np
import mediapipe as mp
from ultralytics import YOLO

# 1. Load the original robust YOLO Pose Model
yolo_model = YOLO("yolo11m-pose.pt")

# Initialize MediaPipe strictly for fine-grained foot tracking
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.2)

input_folder = "input_images/"
output_folder = "output_yolo_native_feet/"
os.makedirs(output_folder, exist_ok=True)

# Standard YOLO COCO Connections (Stops right at the ankles)
YOLO_LINKS = [
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),       # Upper body
    (11, 12), (5, 11), (6, 12),                    # Torso
    (11, 13), (13, 15), (12, 14), (14, 16)         # Legs to Ankles
]

# YOLO Ankle Index Definitions
YOLO_L_ANKLE, YOLO_R_ANKLE = 15, 16
# MediaPipe Foot Mapping Definitions
MP_L_ANKLE, MP_L_HEEL, MP_L_TOE = 27, 29, 31
MP_R_ANKLE, MP_R_HEEL, MP_R_TOE = 28, 30, 32

image_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.png')]
print(f"Processing {len(image_files)} files using YOLO skeleton with MediaPipe feet...")

for filename in sorted(image_files):
    img_path = os.path.join(input_folder, filename)
    image = cv2.imread(img_path)
    if image is None: continue
    
    h, w, _ = image.shape
    skeleton_canvas = np.zeros((h, w, 3), dtype=np.uint8)
    
    # 2. Extract the ultra-stable body coordinates from YOLO
    yolo_results = yolo_model.predict(img_path, imgsz=1280, verbose=False)
    results = yolo_results[0]
    
    if results.keypoints is not None and len(results.keypoints) > 0:
        keypoints_list = results.keypoints.xy.cpu().numpy()
        
        for idx, keypoints in enumerate(keypoints_list):
            random_color = list(np.random.randint(60, 256, size=3, dtype=int))
            bgr_color = [int(c) for c in random_color]

            # A. Draw the original high-accuracy YOLO body framework
            for start_idx, end_idx in YOLO_LINKS:
                kp_start, kp_end = keypoints[start_idx], keypoints[end_idx]
                if np.any(kp_start) and np.any(kp_end):
                    cv2.line(skeleton_canvas, (int(kp_start[0]), int(kp_start[1])), 
                             (int(kp_end[0]), int(kp_end[1])), bgr_color, 4, cv2.LINE_AA)

            # B. Extract foot crop area based on YOLO's lower leg positions
            l_ankle = keypoints[YOLO_L_ANKLE]
            r_ankle = keypoints[YOLO_R_ANKLE]
            
            # Find a bounding area just around the dancer's feet
            valid_ankles = [a for a in [l_ankle, r_ankle] if np.any(a)]
            if valid_ankles:
                ax_coords = [a[0] for a in valid_ankles]
                ay_coords = [a[1] for a in valid_ankles]
                
                fx1, fx2 = int(min(ax_coords) - 60), int(max(ax_coords) + 60)
                fy1, fy2 = int(min(ay_coords) - 40), int(max(ay_coords) + 90)
                
                # Boundary safety clamping
                fx1, fy1 = max(0, fx1), max(0, fy1)
                fx2, fy2 = min(w, fx2), min(h, fy2)
                
                foot_crop = image[fy1:fy2, fx1:fx2]
                if foot_crop.size > 0:
                    crop_rgb = cv2.cvtColor(foot_crop, cv2.COLOR_BGR2RGB)
                    mp_results = pose.process(crop_rgb)
                    
                    if mp_results.pose_landmarks:
                        lm = mp_results.pose_landmarks.landmark
                        f_h, f_w, _ = foot_crop.shape
                        
                        # Helper function to convert MediaPipe crop positions back to global screen coordinates
                        def get_global_pt(mp_idx):
                            pt = lm[mp_idx]
                            if pt.visibility > 0.1:
                                return (fx1 + int(pt.x * f_w), fy1 + int(pt.y * f_h))
                            return None

                        # Track real left and right feet components
                        l_foot_ankle = get_global_pt(MP_L_ANKLE)
                        l_foot_heel  = get_global_pt(MP_L_HEEL)
                        l_foot_toe   = get_global_pt(MP_L_TOE)
                        
                        r_foot_ankle = get_global_pt(MP_R_ANKLE)
                        r_foot_heel  = get_global_pt(MP_R_HEEL)
                        r_foot_toe   = get_global_pt(MP_R_TOE)

                        # Draw Left Foot Map (Snapped onto YOLO Ankle coordinate destination)
                        if np.any(l_ankle) and l_foot_ankle and l_foot_toe and l_foot_heel:
                            y_ank = (int(l_ankle[0]), int(l_ankle[1]))
                            # Project heel and toe relative to the stable YOLO ankle anchor location
                            offset_x = y_ank[0] - l_foot_ankle[0]
                            offset_y = y_ank[1] - l_foot_ankle[1]
                            
                            true_heel = (l_foot_heel[0] + offset_x, l_foot_heel[1] + offset_y)
                            true_toe  = (l_foot_toe[0] + offset_x, l_foot_toe[1] + offset_y)
                            
                            cv2.line(skeleton_canvas, y_ank, true_heel, bgr_color, 4, cv2.LINE_AA)
                            cv2.line(skeleton_canvas, true_heel, true_toe, bgr_color, 4, cv2.LINE_AA)
                            cv2.line(skeleton_canvas, y_ank, true_toe, bgr_color, 4, cv2.LINE_AA)
                            cv2.circle(skeleton_canvas, true_toe, 4, (255, 255, 255), -1, cv2.LINE_AA)

                        # Draw Right Foot Map (Snapped onto YOLO Ankle coordinate destination)
                        if np.any(r_ankle) and r_foot_ankle and r_foot_toe and r_foot_heel:
                            y_ank = (int(r_ankle[0]), int(r_ankle[1]))
                            offset_x = y_ank[0] - r_foot_ankle[0]
                            offset_y = y_ank[1] - r_foot_ankle[1]
                            
                            true_heel = (r_foot_heel[0] + offset_x, r_foot_heel[1] + offset_y)
                            true_toe  = (r_foot_toe[0] + offset_x, r_foot_toe[1] + offset_y)
                            
                            cv2.line(skeleton_canvas, y_ank, true_heel, bgr_color, 4, cv2.LINE_AA)
                            cv2.line(skeleton_canvas, true_heel, true_toe, bgr_color, 4, cv2.LINE_AA)
                            cv2.line(skeleton_canvas, y_ank, true_toe, bgr_color, 4, cv2.LINE_AA)
                            cv2.circle(skeleton_canvas, true_toe, 4, (255, 255, 255), -1, cv2.LINE_AA)

            # C. Draw standard joint nodes over the body frame
            for kp in keypoints:
                if np.any(kp):
                    center = (int(kp[0]), int(kp[1]))
                    cv2.circle(skeleton_canvas, center, 6, (255, 255, 255), -1, cv2.LINE_AA)
                    cv2.circle(skeleton_canvas, center, 6, bgr_color, 2, cv2.LINE_AA)

        # Save output
        output_path = os.path.join(output_folder, filename)
        cv2.imwrite(output_path, skeleton_canvas)
        print(f" Saved structural map with true feet: {output_path}")
    else:
        print(f" Skipped {filename} (Zero joints detected).")

pose.close()
print("\nAll frames compiled successfully using snapped structural framework!")
