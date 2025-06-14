# Isaac Sim WebRTC Streaming Setup

This project provides a shell script to configure and launch NVIDIA Isaac Sim with WebRTC support. After setup, it allows visualization via the `nvidia_webrtc_streaming_client_AppImage`.

## Prerequisites

- NVIDIA Isaac Sim (containerized version)
- Docker with NVIDIA GPU support
- NVIDIA WebRTC Streaming Client (`nvidia_webrtc_streaming_client_AppImage`)
- Linux system with compatible GPU drivers
  
## Clone Robot Arm repository 

- Clone the following repository to the Issac-sim-assets directory https://github.com/TheRobotStudio/SO-ARM100/tree/main

## Usage

### 1. Run the Setup Script

```bash
chmod +x run_issac.sh
./run_issac.sh
```

This script will:

- Pull or run the Isaac Sim Docker container
- Set up necessary **volume mounts** and **environment variables**
- Launch Isaac Sim with WebRTC streaming support

### 2. Download and Launch the WebRTC Streaming Client

After the Isaac Sim is fully started download Issac Sim WebRTC Streaming Client from https://docs.isaacsim.omniverse.nvidia.com/4.5.0/installation/download.html#isaac-sim-latest-release to the project folder and run the following:

```bash
chmod +x isaacsim-webrtc-streaming-client-1.0.6-linux-x64.AppImage
./isaacsim-webrtc-streaming-client-1.0.6-linux-x64.AppImage
```
<!-- 
```bash
chmod +x nvidia_webrtc_streaming_client.AppImage
./nvidia_webrtc_streaming_client.AppImage
``` -->
### 3. Connect to Isaac Sim

In the WebRTC client:

- Press **Connect**
- You should now see the Isaac Sim GUI streamed from the container

## Notes

- Make sure the ports required by Isaac Sim and WebRTC (typically 3009 for signaling) are open and not blocked by a firewall.
- If you experience connectivity issues, ensure that `localhost` or the container’s IP is reachable and the signaling server is correctly configured.

## Files
- `run_issac.sh`: Script that launches Isaac Sim with required configuration
- `nvidia_webrtc_streaming_client.AppImage`: Standalone binary to connect to the Isaac Sim instance via WebRTC

## Environment Variables and Mounts

The script automatically sets the necessary environment variables and mounts volumes like:

- `~/docker/isaac-sim` to `/isaac-sim`
- Persistent caching and configuration directories
- Audio and display forwarding for WebRTC support
