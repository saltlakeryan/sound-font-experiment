#!/bin/bash
set -e

echo "=== 1. Recreating Project Directory ==="
rm -rf advanced-singing-synth || true
mkdir -p advanced-singing-synth
cd advanced-singing-synth

echo "=== 2. Creating python files ==="

# Create the FastAPI backend application
cat << 'EOF' > app.py
import os
import io
import torch
import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openvoice import se_extractor
from openvoice.api import ToneColorConverter
from melo.api import TTS

app = FastAPI()

device = "cuda" if torch.cuda.is_available() else "cpu"
ckpt_converter = 'checkpoints_v2/converter'

# Initialize MeloTTS as the base speaker engine for OpenVoice V2
base_tts = TTS(language='EN', device=device)
speaker_id = base_tts.hps.data.spk2id['EN-Default']

tone_color_converter = ToneColorConverter(f'{ckpt_converter}/config.json', device=device)
tone_color_converter.load_ckpt(f'{ckpt_converter}/checkpoint.pth')

source_se = torch.load('checkpoints_v2/base_speakers/ses/en-default.pth', map_location=device)

class TTSRequest(BaseModel):
    text: str
    pitch_scale: float = 1.0

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/synthesize")
async def synthesize(request: TTSRequest):
    try:
        output_path = "temp_output.wav"
        # Generate base audio using MeloTTS
        base_tts.tts_to_file(text=request.text, speaker_id=speaker_id, output_path=output_path, speed=0.8)
        
        # OpenVoice V2 ToneColorConverter does not natively support a 'pitch_scale' parameter.
        # Instead of extracting target_se dynamically (which fails for short syllable inputs),
        # we perform identity tone conversion to match the default speaker, then pitch shift via librosa.
        converted_audio = tone_color_converter.convert(
            audio_src_path=output_path, 
            src_se=source_se, 
            tgt_se=source_se, 
            output_path=None
        )
        
        if request.pitch_scale != 1.0:
            import numpy as np
            import librosa
            n_steps = 12 * np.log2(request.pitch_scale)
            pitched_audio = librosa.effects.pitch_shift(converted_audio, sr=24000, n_steps=n_steps)
        else:
            pitched_audio = converted_audio

        buffer = io.BytesIO()
        sf.write(buffer, pitched_audio, 24000, format='WAV', subtype='PCM_16')
        buffer.seek(0)
        
        if os.path.exists(output_path):
            os.remove(output_path)
            
        return StreamingResponse(buffer, media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Create the orchestration script that handles hitting the API and stitching
cat << 'EOF' > orchestrator.py
import requests
import wave
import time
import sys
from io import BytesIO

print("Waiting for OpenVoice API container to initialize...", flush=True)
for i in range(30):
    try:
        res = requests.get("http://api:8000/health", timeout=2)
        if res.status_code == 200:
            print("API is online! Starting synthesis...", flush=True)
            break
    except requests.exceptions.ConnectionError:
        time.sleep(2)
else:
    print("API failed to initialize in time.", flush=True)
    sys.exit(1)

scale_steps = [
    ("do", 0.75),
    ("re", 0.84),
    ("mi", 0.93),
    ("fa", 1.02),
    ("so", 1.11),
    ("la", 1.20),
    ("ti", 1.29),
    ("do", 1.38)
]

combined_frames = []
params = None

for word, pitch in scale_steps:
    try:
        print(f"Synthesizing note: {word} (scale: {pitch})", flush=True)
        response = requests.post("http://api:8000/synthesize", json={
            "text": f"{word}...", 
            "pitch_scale": pitch
        })
        
        if response.status_code != 200:
            print(f"Error generating {word}: {response.text}", flush=True)
            sys.exit(1)
            
        with wave.open(BytesIO(response.content), 'rb') as w:
            if not params:
                params = w.getparams()
            combined_frames.append(w.readframes(w.getnframes()))
    except Exception as e:
        print(f"Connection failed during synthesis: {e}", flush=True)
        sys.exit(1)

output_filepath = "/output/do-re-me-fa-so-la-ti-do.wav"
with wave.open(output_filepath, "wb") as output_file:
    output_file.setparams(params)
    for frame in combined_frames:
        output_file.writeframes(frame)

print(f"\nFile successfully created in your local directory: do-re-me-fa-so-la-ti-do.wav", flush=True)
EOF

echo "=== 3. Creating Clean Dockerfile ==="
cat << 'EOF' > Dockerfile
FROM python:3.10-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    wget \
    unzip \
    libsndfile1 \
    ffmpeg \
    build-essential \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip "setuptools<82" wheel

# Install PyTorch and related audio/vision packages targeting the CPU wheel index
RUN pip install --no-cache-dir torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir "cython<3"
RUN pip install --no-cache-dir --no-build-isolation av==10.0.0

# Clone the official OpenVoice repository and install it in editable mode
RUN git clone https://github.com/myshell-ai/OpenVoice.git . && \
    pip install --no-cache-dir -e .

# Install MeloTTS as required by OpenVoice V2 and pre-download linguistic datasets
RUN pip install --no-cache-dir git+https://github.com/myshell-ai/MeloTTS.git && \
    python -m nltk.downloader averaged_perceptron_tagger averaged_perceptron_tagger_eng punkt && \
    python -m unidic download

# Patch se_extractor.py to dynamically select CPU/CUDA execution for WhisperModel to prevent GPU-only crashes
RUN sed -i 's/device="cuda", compute_type="float16"/device="cuda" if torch.cuda.is_available() else "cpu", compute_type="float16" if torch.cuda.is_available() else "float32"/g' openvoice/se_extractor.py

# Download and extract OpenVoice V2 model checkpoints
RUN wget -q https://huggingface.co/kevinwang676/openvocie-v2/resolve/main/checkpoints_v2_0417.zip && \
    unzip checkpoints_v2_0417.zip && \
    rm checkpoints_v2_0417.zip

RUN pip install --no-cache-dir fastapi uvicorn pydantic soundfile requests "setuptools<82"

COPY app.py /app/app.py
COPY orchestrator.py /app/orchestrator.py

EXPOSE 8000
EOF

echo "=== 4. Creating docker-compose file ==="
cat << 'EOF' > docker-compose.yml
services:
  api:
    build: .
    command: python app.py
    expose:
      - "8000"

  orchestrator:
    build: .
    command: python orchestrator.py
    depends_on:
      - api
    volumes:
      - .:/output
EOF

echo "=== 5. Building Docker Images (Enforcing Uncached Resolution...) ==="
# Adding --no-cache directly here to wipe out the broken cached layers
docker compose build --no-cache

echo "=========================================================="
echo "Setup complete!"
echo "To generate your singing neural scale, run this command:"
echo "=========================================================="
echo "docker compose run --rm orchestrator"
