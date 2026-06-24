import cv2
import numpy as np
from ultralytics import YOLO

# 1. Load the pre-trained segmentation model
model = YOLO("yolo11n-seg.pt")  

# 2. Run inference on your dancer image
image_path = "dancers.jpg"
results = model(image_path)[0]

# Ensure masks were detected
if results.masks is not None:
    orig_img = results.orig_img
    h, w, _ = orig_img.shape

    # Initialize blank canvases for silhouettes
    combined_mask = np.zeros((h, w), dtype=np.uint8)
    individual_canvas = np.zeros((h, w, 3), dtype=np.uint8)

    # Filter out only "person" detections (COCO class 0)
    for mask, box in zip(results.masks.data, results.boxes):
        class_id = int(box.cls[0])
        if class_id == 0:  # Class 0 is human/person
            
            # Resize the low-res model mask back to original image size
            mask_np = mask.cpu().numpy()
            mask_resized = cv2.resize(mask_np, (w, h), interpolation=cv2.INTER_NEAREST).astype(np.uint8)

            # --- APPROACH A: Combined Silhouette ---
            # Use bitwise OR to merge overlapping dancer shapes
            combined_mask = cv2.bitwise_or(combined_mask, mask_resized)

            # --- APPROACH B: Individual Silhouettes ---
            # Give each overlapping dancer a unique color layer
            random_color = list(np.random.random(size=3) * 255)
            individual_canvas[mask_resized == 1] = random_color

    # 3. Finalize and convert the masks
    # Convert combined mask to a stark black silhouette on a white canvas
    final_combined = np.ones_like(orig_img) * 255
    final_combined[combined_mask == 1] = [0, 0, 0] # Black silhouette

    # 4. Save results
    cv2.imwrite("combined_silhouette.jpg", final_combined)
    cv2.imwrite("individual_colored_silhouettes.jpg", individual_canvas)
    print("Silhouettes generated and saved successfully!")
else:
    print("No people detected in the image.")
