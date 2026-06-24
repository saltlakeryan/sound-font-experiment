import os
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

# 1. Load the Medium model
model = YOLO("yolo11m-seg.pt")  

# 2. Define your directories
input_folder = "input_images/"
output_folder = "output_silhouettes/"
os.makedirs(output_folder, exist_ok=True)

# 3. Run inference on the entire folder at once
# This returns a list containing one result object per image found
print(f"Processing all images in '{input_folder}'...")
results_list = model.predict(input_folder, imgsz=1280, retina_masks=True)

# 4. Loop through the results of each individual image
for results in results_list:
    # Get the original image filename (e.g., "dancer_01.png")
    img_path = Path(results.path)
    filename = img_path.name
    
    if results.masks is not None:
        orig_img = results.orig_img
        h, w, _ = orig_img.shape

        # Create a blank black canvas for this image
        final_canvas = np.zeros((h, w, 3), dtype=np.uint8)

        # Loop through each detected person in this specific image
        for mask, box in zip(results.masks.data, results.boxes):
            if int(box.cls) == 0:  # Isolate person class
                mask_np = mask.cpu().numpy()
                
                # High-res smoothing pipeline
                mask_resized = cv2.resize(mask_np, (w, h), interpolation=cv2.INTER_CUBIC)
                mask_8bit = (mask_resized * 255).astype(np.uint8)
                
                smoothed_mask = cv2.GaussianBlur(mask_8bit, (5, 5), 0)
                _, binary_mask = cv2.threshold(smoothed_mask, 127, 255, cv2.THRESH_BINARY)
                
                # Color application
                random_color = list(np.random.randint(0, 256, size=3, dtype=int))
                bgr_color = [int(x) for x in random_color] 
                
                final_canvas[binary_mask == 255] = bgr_color

        # Save the finalized canvas to the output directory using the same name
        output_path = os.path.join(output_folder, filename)
        cv2.imwrite(output_path, final_canvas)
        print(f"Saved high-res silhouette: {output_path}")
    else:
        print(f"No dancers found in {filename}, skipping.")

print("\nAll images processed successfully!")
