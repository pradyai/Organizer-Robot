FROM python:3.10-slim

# Install only essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libc6-dev \
    libglx-mesa0 \
    libgl1 \
    libglew2.2 \
    libosmesa6 \
    libglib2.0-0 \
    patchelf \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /workspace

COPY . /workspace

# Install minimal Python packages
RUN pip install --no-cache-dir \
    mujoco \
    numpy
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -r requirements-extra.txt
# Set environment variables for headless rendering
ENV MUJOCO_GL=osmesa
ENV PYOPENGL_PLATFORM=osmesa

# Create working directory
