import os
import cv2
import numpy as np
import mediapipe as mp

# Initialize MediaPipe Pose Engine
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5)

input_folder = "input_images/"
output_folder = "output_mediapipe_skeletons/"
os.makedirs(output_folder, exist_ok=True)

# Main skeletal connections mapping to join limbs
BODY_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), # Arms & Shoulders
    (11, 23), (12, 24), (23, 24),                    # Torso
    (23, 25), (25, 27), (24, 26), (26, 28)           # Legs down to ankles
]

# NATIVE FOOT TRACKING CONNECTIONS (Ankle -> Heel -> Toe Tip)
FOOT_CONNECTIONS = [
    (27, 29), (29, 31), (27, 31), # Left Foot triangle
    (28, 30), (30, 32), (28, 32)  # Right Foot triangle
]

image_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.png')]
print(f"Found {len(image_files)} PNG files to process with native feet markers.")

for filename in sorted(image_files):
    img_path = os.path.join(input_folder, filename)
    image = cv2.imread(img_path)
    if image is None: continue
    
    h, w, _ = image.shape
    skeleton_canvas = np.zeros((h, w, 3), dtype=np.uint8)
    
    # MediaPipe processes images in RGB format
    rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb_img)
    
    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark
        
        # Extract pixel coordinates into a clean dictionary lookup table
        coords = {}
        for idx, lm in enumerate(landmarks):
            # MediaPipe normalized coordinates (0.0 to 1.0) multiplied by dimensions
            cx, cy = int(lm.x * w), int(lm.y * h)
            # Filter out poor confidence tracking points
            coords[idx] = (cx, cy) if lm.visibility > 0.5 else None

        # Draw the standard body structure lines
        for start, end in BODY_CONNECTIONS:
            if coords[start] and coords[end]:
                cv2.line(skeleton_canvas, coords[start], coords[end], (0, 255, 0), 4, cv2.LINE_AA)

        # Draw the actual traced feet boundaries (Ankle -> Heel -> Toe)
        for start, end in FOOT_CONNECTIONS:
            if coords[start] and coords[end]:
                # Draw the foot tracking lines in a distinct bright color
                cv2.line(skeleton_canvas, coords[start], coords[end], (255, 100, 0), 4, cv2.LINE_AA)

        # Stencil small white marker dots directly over every valid tracked joint
        for idx, pt in coords.items():
            if pt:
                cv2.circle(skeleton_canvas, pt, 5, (255, 255, 255), -1, cv2.LINE_AA)

        # Instantly stream file out to drive
        output_path = os.path.join(output_folder, filename)
        cv2.imwrite(output_path, skeleton_canvas)
        print(f" Saved native foot tracking map: {output_path}")
    else:
        print(f" Skipped {filename} (No dancer structural markers found).")

pose.close()
print("\nProcessing complete!")
