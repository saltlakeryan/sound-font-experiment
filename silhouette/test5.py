import os
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

# 1. Load the Medium Pose model (inherently maps 17 key joints)
model = YOLO("yolo11m-pose.pt")  

# 2. Setup directories
input_folder = "input_images/"
output_folder = "output_skeletons/"
os.makedirs(output_folder, exist_ok=True)

# Define the standard skeleton connection map (which joints connect to which)
# Pairs connect bones: e.g., (5, 7) is Left Shoulder to Left Elbow
SKELETON_LINKS = [
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),       # Upper body (Shoulders & Arms)
    (11, 12), (5, 11), (6, 12),                    # Torso frame
    (11, 13), (13, 15), (12, 14), (14, 16)         # Lower body (Hips & Legs)
]

print(f"Processing structural skeletons in '{input_folder}'...")
results_list = model.predict(input_folder, imgsz=1280)

# 3. Loop through images
for results in results_list:
    img_path = Path(results.path)
    filename = img_path.name
    
    if results.keypoints is not None and len(results.keypoints) > 0:
        orig_img = results.orig_img
        h, w, _ = orig_img.shape

        # Create a clean black canvas for the lines
        skeleton_canvas = np.zeros((h, w, 3), dtype=np.uint8)

        # Extract coordinates data (batch, joints, xy)
        # .xy returns raw original-resolution pixels natively
        keypoints_list = results.keypoints.xy.cpu().numpy()

        # Loop through each detected dancer
        for keypoints in keypoints_list:
            # Generate a unique color for this specific dancer's stick figure
            random_color = list(np.random.randint(50, 256, size=3, dtype=int))
            bgr_color = [int(x) for x in random_color]

            # Draw the Bones (Lines connecting joints)
            for start_idx, end_idx in SKELETON_LINKS:
                kp_start = keypoints[start_idx]
                kp_end = keypoints[end_idx]

                # Only draw lines if BOTH joints are detected (coordinates aren't 0,0)
                if np.any(kp_start) and np.any(kp_end):
                    pt1 = (int(kp_start[0]), int(kp_start[1]))
                    pt2 = (int(kp_end[0]), int(kp_end[1]))
                    
                    # Draw anti-aliased clean vector lines (thickness=4)
                    cv2.line(skeleton_canvas, pt1, pt2, bgr_color, thickness=4, lineType=cv2.LINE_AA)

            # Draw the Joints (Small circles on top of the lines)
            for kp in keypoints:
                if np.any(kp):
                    center = (int(kp[0]), int(kp[1]))
                    # Slightly brighter center node for visual contrast
                    cv2.circle(skeleton_canvas, center, radius=6, color=(255, 255, 255), thickness=-1, lineType=cv2.LINE_AA)
                    cv2.circle(skeleton_canvas, center, radius=6, color=bgr_color, thickness=2, lineType=cv2.LINE_AA)

        # Save output frame
        output_path = os.path.join(output_folder, filename)
        cv2.imwrite(output_path, skeleton_canvas)
        print(f"Saved high-res skeleton: {output_path}")
    else:
        print(f"No skeletons detected in {filename}, skipping.")

print("\nAll skeleton structures processed successfully!")
