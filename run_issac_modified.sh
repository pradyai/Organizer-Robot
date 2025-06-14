#!/bin/bash

set -e

ISAAC_IMAGE="nvcr.io/nvidia/isaac-sim:4.5.0"
CONTAINER_NAME="isaac-sim"
CACHE_DIR="$HOME/docker/isaac-sim"
ASSET_VOLUME="$PWD/issac_sim_assets"
ROS_DOMAIN_ID=0

# Verify the folder exists
if [ ! -d "$ASSET_VOLUME" ]; then
  echo "ERROR: Asset volume directory not found at: $ASSET_VOLUME"
  echo "Please make sure it exists relative to this script."
  exit 1
fi

# Check NVIDIA driver version
echo "Checking NVIDIA driver version..."
REQUIRED_VERSION=535
DRIVER_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -n1 | cut -d. -f1)

if [[ "$DRIVER_VERSION" -lt "$REQUIRED_VERSION" ]]; then
  echo "ERROR: NVIDIA driver version must be >= $REQUIRED_VERSION. Current: $DRIVER_VERSION"
  exit 1
fi

echo "NVIDIA driver check passed: $DRIVER_VERSION"

# Ensure cache directories exist
mkdir -p "$CACHE_DIR/cache/ov" "$CACHE_DIR/cache/pip" "$CACHE_DIR/cache/glcache" "$CACHE_DIR/cache/computecache" "$CACHE_DIR/cache/asset_browser" "$CACHE_DIR/logs" "$CACHE_DIR/data" "$CACHE_DIR/pkg" "$CACHE_DIR/documents"

# Pull image if not present
if ! docker image inspect "$ISAAC_IMAGE" > /dev/null 2>&1; then
  echo "Pulling Isaac Sim Docker image..."
  docker pull "$ISAAC_IMAGE"
else
  echo "Isaac Sim image already exists locally."
fi

# Run the container
echo "Launching Isaac Sim container..."
docker run --name "$CONTAINER_NAME" --entrypoint bash -it --rm \
  --gpus all \
  --network=host \
  --shm-size=8G \
  --memory=16G \
  --cpus=4 \
  -e "ACCEPT_EULA=Y" \
  -e "PRIVACY_CONSENT=Y" \
  -e "ROS_DOMAIN_ID=$ROS_DOMAIN_ID" \
  -v "$CACHE_DIR/cache/ov:/root/.cache/ov:rw" \
  -v "$CACHE_DIR/cache/pip:/root/.cache/pip:rw" \
  -v "$CACHE_DIR/cache/glcache:/root/.cache/nvidia/GLCache:rw" \
  -v "$CACHE_DIR/cache/computecache:/root/.nv/ComputeCache:rw" \
  -v "$CACHE_DIR/cache/asset_browser:/isaac-sim/exts/isaacsim.asset.browser/cache:rw" \
  -v "$CACHE_DIR/logs:/root/.nvidia-omniverse/logs:rw" \
  -v "$CACHE_DIR/data:/root/.local/share/ov/data:rw" \
  -v "$CACHE_DIR/pkg:/root/.local/share/ov/pkg:rw" \
  -v "$CACHE_DIR/documents:/root/Documents:rw" \
  -v "$ASSET_VOLUME:/root/isaac-sim/user_data:rw" \
  "$ISAAC_IMAGE" -c "./runheadless.sh -v"
