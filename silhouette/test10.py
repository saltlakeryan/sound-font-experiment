import os
import cv2
import numpy as np
from ultralytics import YOLO

# 1. Initialize both models
seg_model = YOLO("yolo11m-seg.pt")   # For high-res silhouettes
pose_model = YOLO("yolo11m-pose.pt") # For internal bone structures

input_folder = "input_images/"
output_folder = "output_combined_graphics/"
os.makedirs(output_folder, exist_ok=True)

# Standard YOLO COCO Connections (Stops at ankles)
SKELETON_LINKS = [
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),       # Upper body
    (11, 12), (5, 11), (6, 12),                    # Torso
    (11, 13), (13, 15), (12, 14), (14, 16)         # Legs
]

image_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.png')]
print(f"Generating combined graphics for {len(image_files)} files...")

for filename in sorted(image_files):
    img_path = os.path.join(input_folder, filename)
    image = cv2.imread(img_path)
    if image is None: continue
    
    h, w, _ = image.shape
    final_canvas = np.zeros((h, w, 3), dtype=np.uint8)
    
    # 2. Run segmentation and pose models on the same frame
    seg_results = seg_model.predict(img_path, imgsz=1280, retina_masks=True, verbose=False)[0]
    pose_results = pose_model.predict(img_path, imgsz=1280, verbose=False)[0]
    
    # Track assigned colors to pair matching individuals
    # We match them up based on bounding box centers
    dancer_layers = []

    # --- LAYER 1: Generate & Smooth Silhouettes ---
    if seg_results.masks is not None:
        for mask, box in zip(seg_results.masks.data, seg_results.boxes):
            if int(box.cls) == 0:
                mask_np = mask.cpu().numpy()
                
                # High-res smoothing pipeline
                mask_resized = cv2.resize(mask_np, (w, h), interpolation=cv2.INTER_CUBIC)
                mask_8bit = (mask_resized * 255).astype(np.uint8)
                smoothed_mask = cv2.GaussianBlur(mask_8bit, (5, 5), 0)
                _, binary_mask = cv2.threshold(smoothed_mask, 127, 255, cv2.THRESH_BINARY)
                
                # Generate unique color for this silhouette shape
                color = list(np.random.randint(40, 200, size=3, dtype=int))
                bgr_color = [int(c) for c in color]
                
                # Render silhouette shape onto the master canvas
                final_canvas[binary_mask == 255] = bgr_color
                
                # Store box center to map the skeleton later
                xyxy = box.xyxy.cpu().numpy()[0]
                center_x = (xyxy[0] + xyxy[2]) / 2
                dancer_layers.append({'center_x': center_x, 'mask': binary_mask, 'color': bgr_color})

    # --- LAYER 2: Overlay Matching Skeletons ---
    if pose_results.keypoints is not None and len(pose_results.keypoints) > 0:
        keypoints_list = pose_results.keypoints.xy.cpu().numpy()
        pose_boxes = pose_results.boxes.xyxy.cpu().numpy()
        
        for idx, keypoints in enumerate(keypoints_list):
            if int(pose_results.boxes.cls[idx]) != 0: continue
            
            # Find matching silhouette color by comparing horizontal bounding box centers
            p_box = pose_boxes[idx]
            p_center_x = (p_box[0] + p_box[2]) / 2
            
            best_match = None
            min_dist = float('inf')
            for dancer in dancer_layers:
                dist = abs(dancer['center_x'] - p_center_x)
                if dist < min_dist:
                    min_dist = dist
                    best_match = dancer
            
            # Fallback color if no silhouette match is found
            line_color = best_match['color'] if best_match else (255, 255, 255)
            # Make the skeleton bones slightly brighter than the body silhouette for contrast
            skeleton_color = [min(255, c + 50) for c in line_color]

            # Draw the bone lines
            for start_idx, end_idx in SKELETON_LINKS:
                kp_start, kp_end = keypoints[start_idx], keypoints[end_idx]
                if np.any(kp_start) and np.any(kp_end):
                    pt1 = (int(kp_start[0]), int(kp_start[1]))
                    pt2 = (int(kp_end[0]), int(kp_end[1]))
                    cv2.line(final_canvas, pt1, pt2, skeleton_color, thickness=3, lineType=cv2.LINE_AA)

            # Draw the joint nodes
            for kp in keypoints:
                if np.any(kp):
                    center = (int(kp[0]), int(kp[1]))
                    cv2.circle(final_canvas, center, radius=5, color=(255, 255, 255), thickness=-1, lineType=cv2.LINE_AA)
                    cv2.circle(final_canvas, center, radius=5, color=skeleton_color, thickness=2, lineType=cv2.LINE_AA)

    # 3. Stream completed image frame straight to disk
    output_path = os.path.join(output_folder, filename)
    cv2.imwrite(output_path, final_canvas)
    print(f" Saved combined frame: {output_path}")

print("\nAll files successfully processed into combined skeleton-silhouettes!")
