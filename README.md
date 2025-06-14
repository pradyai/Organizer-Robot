# Organizer-Robot
# Project Environment with Docker

This repository is configured to run within a Docker container, allowing for a consistent and isolated development environment.

The main project folder, `Mounted_Repo`, is mounted directly into the container. This means any changes you make to the files on your local machine will be immediately reflected inside the container, and vice-versa.

## Prerequisites

Before you begin, ensure you have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running on your system.

## How to Use 🚀

Follow these steps to build the Docker image and run the container.

### 1. Clone the Repository

First, clone this repository to your local machine.

```bash
git clone <your-repository-url>
cd <your-repo-name>
```

### 2. Build the Docker Image

From the root directory of the project (where the `Dockerfile` is located), run the following command to build the Docker image. We will tag it with the name `my-project-env`.

```bash
docker build -t my-project-env .
```

### 3. Run the Docker Container

Now, run the container. This command does two important things:
* `-d`: Runs the container in detached mode (in the background).
* `-v "$(pwd)/Mounted_Repo:/app/Mounted_Repo"`: Mounts the `Mounted_Repo` directory from your local machine (present working directory) into the `/app/Mounted_Repo` directory inside the container.

```bash
docker run -d --name my-app-container -v "$(pwd)/Mounted_Repo:/app/Mounted_Repo" my-project-env
```
**For Windows Users (PowerShell):**
Use `${pwd}` instead of `$(pwd)`:
```powershell
docker run -it --gpus all --name my-app-container -v "${pwd}/hishamstest:/app/Mounted_Repo" my-project-env bash
```

### 4. Access the Container

Your container is now running with the `Mounted_Repo` folder linked. To access the container's command line (shell), use the `docker exec` command:

```bash
docker exec -it my-app-container bash
```

Once inside, you can navigate and see your mounted files:

```bash
# You are now inside the container's shell at the /app directory
ls

# You should see the Mounted_Repo directory
ls Mounted_Repo
```
You will see the `Hisham`, `Ahmed`, `Pradyumn`, and `Shubham` folders. Any file you create here will appear on your local machine, and any file you modify on your local machine will be updated here.

### 5. Stop the Container

When you are finished, you can stop and remove the container to keep your system clean.

```bash
# Stop the container
docker stop my-app-container

# Optional: Remove the container
docker rm my-app-container
```
### 6. Start the OpenVLA model.

1. make sure you are in the root folder "Organizer-Robot"
2. Run the docker container using the command above - I used VSCode to run the container
3. Run the script openvlatest.py and it (hopefully) works. 
4. The output should contain an array of coordinates, as documented in OpenVLA.
5. You can upload your own picture and modify the instruction

# MuJoCo-Specific Tips
Environment Variables in Container:
    MUJOCO_GL=osmesa for headless rendering
    Mount X11 socket for GUI applications
    Consider using VNC for remote GUI access

# Testing MuJoCo Setup:
import mujoco
import gymnasium as gym

# Test basic MuJoCo functionality
env = gym.make('HalfCheetah-v4')
obs, info = env.reset()
print("MuJoCo setup successful!")

