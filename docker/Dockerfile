FROM python:3.10-slim

# Install system dependencies for MuJoCo
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libosmesa6-dev \
    libgl1-mesa-glx \
    libglfw3 \
    patchelf \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . .

# Install package in development mode
#RUN pip install -e .

# Default command
CMD ["python", "-c", "print('Container ready for development')"]
