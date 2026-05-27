FROM python:3.11-slim-bookworm

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=offscreen

# Install core audio engines, compilation tools, system fonts, and audio client backends
RUN apt-get update && apt-get install -y --no-install-recommends \
    lilypond \
    fluidsynth \
    polyphone \
    xvfb \
    libasound2 \
    shared-mime-info \
    fonts-freefont-ttf \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory inside container
WORKDIR /app

# Copy the python script into the container image
COPY generator.py .

# Trigger execution when the container starts up
CMD ["python", "generator.py"]
