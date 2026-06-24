import os
import math
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

# 1. Load the Medium Pose model
model = YOLO("yolo11m-pose.pt")  

input_folder = "input_images/"
output_folder = "output_skeletons/"
os.makedirs(output_folder, exist_ok=True)

SKELETON_LINKS = [
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),       # Upper body
    (11, 12), (5, 11), (6, 12),                    # Torso
    (11, 13), (13, 15), (12, 14), (14, 16)         # Lower body
]

# Joint indices for calculating angles
LEFT_KNEE, LEFT_ANKLE = 13, 15
RIGHT_KNEE, RIGHT_ANKLE = 14, 16

# Get all valid png images in the directory
image_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.png')]
print(f"Found {len(image_files)} PNG files to process live.")

# 2. Iterate and generate output files on the fly
for filename in sorted(image_files):
    img_path = os.path.join(input_folder, filename)
    
    # Process only this single image frame
    results_list = model.predict(img_path, imgsz=1280, verbose=False)
    results = results_list[0]
    
    if results.keypoints is not None and len(results.keypoints) > 0:
        orig_img = results.orig_img
        h, w, _ = orig_img.shape
        skeleton_canvas = np.zeros((h, w, 3), dtype=np.uint8)
        keypoints_list = results.keypoints.xy.cpu().numpy()

        print(f"\n--- Frame: {filename} ---")

        for idx, keypoints in enumerate(keypoints_list):
            random_color = list(np.random.randint(50, 256, size=3, dtype=int))
            bgr_color = [int(x) for x in random_color]

            # --- ANGLE CALCULATION ---
            # Define helper function to compute angle relative to horizontal ground
            def get_bone_angle(joint_start, joint_end):
                if np.any(joint_start) and np.any(joint_end):
                    dx = joint_end[0] - joint_start[0]
                    dy = joint_end[1] - joint_start[1]  # Image Y goes down
                    # Calculate angle in degrees, inverted dy so upward direction is positive
                    angle = math.degrees(math.atan2(-dy, dx))
                    return round(angle, 1)
                return None

            left_angle = get_bone_angle(keypoints[LEFT_KNEE], keypoints[LEFT_ANKLE])
            right_angle = get_bone_angle(keypoints[RIGHT_KNEE], keypoints[RIGHT_ANKLE])
            
            # Print calculated angles to console as it progresses
            print(f" Dancer #{idx+1}: Left Shin Angle: {left_angle}°, Right Shin Angle: {right_angle}°")

            # Draw bones
            for start_idx, end_idx in SKELETON_LINKS:
                kp_start = keypoints[start_idx]
                kp_end = keypoints[end_idx]
                if np.any(kp_start) and np.any(kp_end):
                    pt1 = (int(kp_start[0]), int(kp_start[1]))
                    pt2 = (int(kp_end[0]), int(kp_end[1]))
                    cv2.line(skeleton_canvas, pt1, pt2, bgr_color, thickness=4, lineType=cv2.LINE_AA)

            # Draw joint nodes
            for kp in keypoints:
                if np.any(kp):
                    center = (int(kp[0]), int(kp[1]))
                    cv2.circle(skeleton_canvas, center, radius=6, color=(255, 255, 255), thickness=-1, lineType=cv2.LINE_AA)
                    cv2.circle(skeleton_canvas, center, radius=6, color=bgr_color, thickness=2, lineType=cv2.LINE_AA)

        # 3. Save file instantly before moving to next image
        output_path = os.path.join(output_folder, filename)
        cv2.imwrite(output_path, skeleton_canvas)
        print(f" Completed & Saved: {output_path}")
    else:
        print(f"Skipped {filename} (No dancers detected).")

print("\nAll sequential files processed and written successfully!")
