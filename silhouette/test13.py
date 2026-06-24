import os
import cv2
import json
import numpy as np
from ultralytics import YOLO

# 1. Initialize models
seg_model = YOLO("yolo11m-seg.pt")   
pose_model = YOLO("yolo11m-pose.pt") 

input_folder = "input_images/"
output_folder = "output_combined_graphics/"
os.makedirs(output_folder, exist_ok=True)

SKELETON_LINKS = [
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),       # Upper body
    (11, 12), (5, 11), (6, 12),                    # Torso
    (11, 13), (13, 15), (12, 14), (14, 16)         # Legs
]

# Preset mappings
PRESETS = {
    "white": {"body": (245, 245, 245), "bone": (20, 20, 20), "outline": (0, 0, 0)},
    "black": {"body": (40, 40, 40),    "bone": (255, 255, 255), "outline": (255, 255, 255)}
}
DANCER_PRESETS_LIST = [PRESETS["white"], PRESETS["black"]]

# Load map.json override if it exists
map_path = os.path.join(input_folder, "map.json")
manual_map = {}
if os.path.exists(map_path):
    with open(map_path, "r") as f:
        manual_map = json.load(f)
    print(f" Loaded manual override map with {len(manual_map)} framed rules.")

image_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith('.png')])
print(f"Generating graphics for {len(image_files)} files...")

for filename in image_files:
    img_path = os.path.join(input_folder, filename)
    image = cv2.imread(img_path)
    if image is None: continue
    
    h, w, _ = image.shape
    final_canvas = np.ones((h, w, 3), dtype=np.uint8) * 255
    
    # Extract the first element [0] from the prediction list output
    seg_results = seg_model.track(img_path, imgsz=1280, retina_masks=True, persist=True, verbose=False)[0]
    pose_results = pose_model.track(img_path, imgsz=1280, persist=True, verbose=False)[0]
    
    dancer_layers = []
    has_override = filename in manual_map

    # --- LAYER 1: Silhouette Rendering ---
    if seg_results.masks is not None:
        seg_detections = list(zip(seg_results.masks.data, seg_results.boxes))
        
        # Sort left-to-right immediately to handle manual overrides properly
        seg_detections.sort(key=lambda x: float((x[1].xyxy[0][0] + x[1].xyxy[0][2]) / 2))
        
        has_ids = seg_results.boxes.id is not None
        
        for idx, (mask, box) in enumerate(seg_detections):
            if int(box.cls) == 0:
                mask_np = mask.cpu().numpy()
                
                mask_resized = cv2.resize(mask_np, (w, h), interpolation=cv2.INTER_CUBIC)
                mask_8bit = (mask_resized * 255).astype(np.uint8)
                smoothed_mask = cv2.GaussianBlur(mask_8bit, (5, 5), 0)
                _, binary_mask = cv2.threshold(smoothed_mask, 127, 255, cv2.THRESH_BINARY)
                
                # CHOOSE COLOR: JSON override vs AI tracking ID vs Horizontal loop position
                if has_override:
                    color_choices = manual_map[filename]
                    color_key = color_choices[idx % len(color_choices)]
                    preset = PRESETS.get(color_key.lower(), PRESETS["white"])
                elif has_ids and box.id is not None:
                    track_id = int(box.id.item())
                    preset = DANCER_PRESETS_LIST[(track_id - 1) % len(DANCER_PRESETS_LIST)]
                else:
                    preset = DANCER_PRESETS_LIST[idx % len(DANCER_PRESETS_LIST)]
                
                # Paint silhouette
                final_canvas[binary_mask == 255] = preset["body"]
                
                # Draw crisp outline
                contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(final_canvas, contours, -1, preset["outline"], thickness=2, lineType=cv2.LINE_AA)
                
                xyxy = box.xyxy[0].cpu().numpy()
                center_x = (xyxy[0] + xyxy[2]) / 2
                dancer_layers.append({'center_x': center_x, 'preset': preset})

    # --- LAYER 2: Overlaying Skeletons ---
    if pose_results.keypoints is not None and len(pose_results.keypoints) > 0:
        keypoints_list = pose_results.keypoints.xy.cpu().numpy()
        pose_boxes = pose_results.boxes.xyxy.cpu().numpy()
        
        for idx, keypoints in enumerate(keypoints_list):
            if int(pose_results.boxes.cls[idx]) != 0: continue
            
            p_box = pose_boxes[idx]
            p_center_x = (p_box[0] + p_box[2]) / 2
            
            best_match = None
            min_dist = float('inf')
            for dancer in dancer_layers:
                dist = abs(dancer['center_x'] - p_center_x)
                if dist < min_dist:
                    min_dist = dist
                    best_match = dancer
            
            bone_color = best_match['preset']["bone"] if best_match else (0, 0, 0)

            # Draw bones
            for start_idx, end_idx in SKELETON_LINKS:
                kp_start, kp_end = keypoints[start_idx], keypoints[end_idx]
                if np.any(kp_start) and np.any(kp_end):
                    pt1 = (int(kp_start[0]), int(kp_start[1]))
                    pt2 = (int(kp_end[0]), int(kp_end[1]))
                    cv2.line(final_canvas, pt1, pt2, bone_color, thickness=3, lineType=cv2.LINE_AA)

            # Draw joints
            for kp in keypoints:
                if np.any(kp):
                    center = (int(kp[0]), int(kp[1]))
                    node_bg = (255, 255, 255) if bone_color == (0, 0, 0) else (0, 0, 0)
                    cv2.circle(final_canvas, center, radius=5, color=node_bg, thickness=-1, lineType=cv2.LINE_AA)
                    cv2.circle(final_canvas, center, radius=5, color=bone_color, thickness=2, lineType=cv2.LINE_AA)

    output_path = os.path.join(output_folder, filename)
    cv2.imwrite(output_path, final_canvas)
    if has_override:
        print(f" Saved frame {filename} (Using Manual Override Map)")
    else:
        print(f" Saved frame {filename} (Using AI Tracking)")

print("\nAll frames compiled! Check output directory.")
