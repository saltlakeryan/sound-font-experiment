FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=offscreen

RUN apt-get update && apt-get install -y --no-install-recommends \
    lilypond \
    fluidsynth \
    polyphone \
    xvfb \
    xauth \
    libasound2 \
    shared-mime-info \
    fonts-freefont-ttf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# The entrypoint directly executes whatever generator script is mounted to the file system
CMD ["python", "generator.py"]
