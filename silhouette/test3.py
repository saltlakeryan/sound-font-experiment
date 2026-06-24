import cv2
import numpy as np
from ultralytics import YOLO

# 1. Load the Medium model for better edge detection accuracy on limbs
model = YOLO("yolo11m-seg.pt")  

image_path = "dancers.jpg"

# 2. Run high-res inference with native retina masks enabled
results = model.predict(image_path, imgsz=1280, retina_masks=True)

if results[0].masks is not None:
    orig_img = results[0].orig_img
    h, w, _ = orig_img.shape

    # Create a blank black canvas for the final colored output
    final_canvas = np.zeros((h, w, 3), dtype=np.uint8)

    # Loop through each detection individualy
    for mask, box in zip(results[0].masks.data, results[0].boxes):
        if int(box.cls) == 0:  # Isolate person class
            mask_np = mask.cpu().numpy()
            
            # --- HIGH-RES SMOOTHING PIPELINE (PER PERSON) ---
            # Step A: Resize raw probability float map with Bicubic interpolation
            mask_resized = cv2.resize(mask_np, (w, h), interpolation=cv2.INTER_CUBIC)
            mask_8bit = (mask_resized * 255).astype(np.uint8)
            
            # Step B: Soften blocky stair-step artifacts
            smoothed_mask = cv2.GaussianBlur(mask_8bit, (5, 5), 0)
            
            # Step C: Re-sharpen into a crisp, binary individual mask
            _, binary_mask = cv2.threshold(smoothed_mask, 127, 255, cv2.THRESH_BINARY)
            
            # --- COLOR APPLICATION ---
            # Generate a distinct random BGR color for this specific dancer
            random_color = list(np.random.randint(0, 256, size=3, dtype=int))
            # Convert python integers to native types OpenCV understands
            bgr_color = [int(x) for x in random_color] 
            
            # Paint this dancer onto the master canvas using their unique smoothed mask
            final_canvas[binary_mask == 255] = bgr_color

    # 3. Save the crisp, multi-colored output
    cv2.imwrite("high_res_individual_colored_silhouettes.jpg", final_canvas)
    print("High-res individual colored silhouettes successfully saved!")
else:
    print("No dancers found.")
