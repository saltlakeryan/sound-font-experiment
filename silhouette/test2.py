import cv2
import numpy as np
from ultralytics import YOLO

# 1. Load the model
model = YOLO("yolo11n-seg.pt")  

image_path = "dancers.jpg"

# 2. OPTIMIZATION: Process at higher input size & use native high-res retina masks
results = model.predict(image_path, imgsz=1280, retina_masks=True)[0]

if results.masks is not None:
    orig_img = results.orig_img
    h, w, _ = orig_img.shape

    # Canvas to collect raw probability float masks
    accumulated_mask = np.zeros((h, w), dtype=np.float32)

    for mask, box in zip(results.masks.data, results.boxes):
        if int(box.cls) == 0:  # Isolate person class
            mask_np = mask.cpu().numpy()
            
            # OPTIMIZATION: Resize using CUBIC (Bicubic) interpolation instead of NEAREST
            # This generates soft, fractional edges instead of harsh blocks
            mask_resized = cv2.resize(mask_np, (w, h), interpolation=cv2.INTER_CUBIC)
            
            # Merge masks together as floating-point probabilities
            accumulated_mask = np.maximum(accumulated_mask, mask_resized)

    # 3. OPTIMIZATION: Sub-pixel edge smoothing and cleanup
    # Convert probability float map to standard 8-bit image
    accumulated_mask = (accumulated_mask * 255).astype(np.uint8)
    
    # Mild Gaussian blur to average out remaining stair-step artifacts
    smoothed_mask = cv2.GaussianBlur(accumulated_mask, (5, 5), 0)
    
    # Precise thresholding to reconstruct clean, sharp binary bounds
    _, final_binary = cv2.threshold(smoothed_mask, 127, 255, cv2.THRESH_BINARY)

    # 4. Generate the final output look
    # Create white canvas
    high_res_silhouette = np.ones_like(orig_img) * 255
    # Paint silhouette pixels black
    high_res_silhouette[final_binary == 255] = 0

    # Save output
    cv2.imwrite("high_res_combined_silhouette.jpg", high_res_silhouette)
    print("High-res silhouette successfully generated!")
else:
    print("No dancers found.")
