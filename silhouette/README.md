# 🕺 AI Dancer Silhouette & Structural Skeleton Generator

A high-performance Python toolset that extracts high-resolution human silhouettes and anatomical skeleton maps from a sequential folder of images. Designed specifically to handle overlapping dancers with a high-contrast palette optimized for sharp black-and-white printing.

## ✨ Features
* **Dual AI Analysis:** Uses YOLOv11 Segmentation (`yolo11m-seg`) for fluid silhouettes and YOLOv11 Pose (`yolo11m-pose`) for structural bones.
* **Overlapping Identity Lock:** Utilizes object tracking engine algorithms alongside a JSON-based manual map override lookup system to keep colors consistent when dancers cross paths.
* **Print-Ready Optimization:** Generates high-contrast vectors (Off-White vs. Dark Charcoal) on a pure white canvas to save ink and ensure readability in grayscale print.
* **Sub-Pixel Edge Smoothing:** Applies Bicubic interpolation and Gaussian blurring to clean up jagged pixel edges.

---

## 📋 Prerequisites & Requirements

This pipeline requires a clean environment running **Python 3.12**. Using Python 3.13 or 3.14 will cause installation errors because underlying libraries (like `lapx`) do not have compiled packages for those versions yet.

### 1. Environment Setup (Using `uv`)
We use `uv` by Astral because it handles Python version compilation and isolated virtual environments significantly faster than standard legacy managers.

```bash
# Install uv onto your Mac system
curl -LsSf https://astral.sh | sh

# Restart your terminal application, then navigate to your workspace
cd /Users/ryan/dev/silhouette/

# Initialize an isolated virtual environment locked to Python 3.12
uv venv --python 3.12

# Activate your newly created environment workspace
source .venv/bin/activate
```

### 2. Dependency Configuration (`requirements.txt`)
Ensure your `requirements.txt` file contains the exact packages needed to prevent runtime dependency resolution loops:

```text
ultralytics>=8.3.0
opencv-python>=4.8.0
numpy>=1.24.0
lapx>=0.5.12
```

Install them into your activated virtual environment using:
```bash
uv pip install -r requirements.txt
```

---

## 🎬 How to Capture Frame Sequences (VLC Shortcut)

If you are starting from a source video file, you can easily generate the required raw image frames using VLC Media Player:

1. Open your dancer video inside **VLC**.
2. Advance the playback to your desired sequence start point.
3. Press **`Command + Option + S`** (Mac OS) on your keyboard to instantly capture a snapshot frame. 
4. Tap your spacebar to move forward frame-by-frame and repeat the shortcut.
5. VLC will dump these sequential files into your system `~/Pictures` folder as zero-loss `.png` formats. Move these into your local `input_images/` directory.

---

## ⚙️ Project File Directory Structure

Set up your project directory files exactly like this before launching your script execution loops:

```text
silhouette/
├── .venv/                      # Managed by uv
├── input_images/               # Put your source VLC captured PNG files here
│   ├── map.json                # Optional: Identity tracking overrides
│   ├── frame_0001.png
│   └── frame_0002.png
├── output_combined_graphics/   # Target folder for generated outlines
├── requirements.txt
└── test13.py                   # Main pipeline script
```

---

## 🛠️ Overlap Color Corrections (`map.json`)

If the AI tracker loses track of identities during intense overlaps or close contact, you can bypass the tracker entirely by placing a `map.json` file inside your `input_images/` folder. 

The configuration maps files by their exact name and assigns colors from **Left-to-Right** based on where the dancers are on the stage screen:

```json
{
  "vlcsnap-2026-06-19-10h20m27s211.png": ["white", "black"],
  "vlcsnap-2026-06-19-10h20m28s315.png": ["black", "white"]
}
```
* `["white", "black"]` forces the leftmost dancer to be rendered in the Off-White preset and the rightmost dancer to be rendered in the Dark Charcoal preset.

---

## 🚀 Execution Command

With your virtual environment active (`source .venv/bin/activate`), run the main processing script:

```bash
python test13.py
```
The program will automatically download the required model weights on the first run, process frames live one-by-one to save system memory, and instantly dump printable files into `output_combined_graphics/`.
