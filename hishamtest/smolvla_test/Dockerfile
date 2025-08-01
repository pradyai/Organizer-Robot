FROM python:3.10-slim

# Avoid interactive prompts during package install
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install required system packages including FFmpeg and its development libraries
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libavfilter-dev \
    libavdevice-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Clone the lerobot repo
RUN git clone https://github.com/huggingface/lerobot.git

# Change working directory to the repo
WORKDIR /app/lerobot

# Install pip dependencies, pin torchvision and torchcodec versions
RUN pip install --upgrade pip && \
    pip install torch==2.6.0 torchvision==0.21.0 torchcodec==0.2.1 && \
    pip install -e ".[smolvla]"

# Default command
CMD ["bash"]
