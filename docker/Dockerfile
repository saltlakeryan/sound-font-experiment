# ==========================================
# STAGE 1: Compilation and Build Environment
# ==========================================
FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Install core compiler toolchain, git, and required development headers
# Added qt6-l10n-tools to provide the missing lrelease binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    qt6-base-dev \
    qt6-base-dev-tools \
    qt6-l10n-tools \
    qt6-svg-dev \
    libasound2-dev \
    libjack-jackd2-dev \
    librtaudio-dev \
    librtmidi-dev \
    libstk-dev \
    libvorbis-dev \
    libogg-dev \
    libflac-dev \
    libssl-dev \
    libsndfile1-dev \
    git \
    ca-certificates \
    libx11-xcb1 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    libxkbcommon-x11-0 \
    libsm6 \
    libice6 \
    xvfb \
    pip \
    python3.12-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# Download Polyphone source directly from GitHub
RUN git clone https://github.com/davy7125/polyphone .

# Edit polyphone.pro to uncomment local fallbacks for RtAudio, RtMidi, and Stk
RUN sed -i 's/#DEFINES += USE_LOCAL_RTAUDIO/DEFINES += USE_LOCAL_RTAUDIO/' sources/polyphone.pro && \
    sed -i 's/#DEFINES += USE_LOCAL_RTMIDI/DEFINES += USE_LOCAL_RTMIDI/' sources/polyphone.pro && \
    sed -i 's/#DEFINES += USE_LOCAL_STK/DEFINES += USE_LOCAL_STK/' sources/polyphone.pro

# Run qmake6 targeting the correct project path and compile
RUN qmake6 sources/polyphone.pro PREFIX=/usr && make -j$(nproc)

RUN ln -s /src/bin/polyphone /usr/bin/polyphone

# Give the container execution permissions
RUN chmod +x /src/bin/polyphone

# =========================================================================
# CACHE SAFE ADDITIONS: X11 & XCB libraries required to stop the Qt crash
# =========================================================================
RUN apt-get update && apt-get install -y --no-install-recommends lilypond \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends fluidsynth \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends python3-pytest

WORKDIR /app
