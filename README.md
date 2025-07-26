# Organizer-Robot
# Project Environment with Docker

# How to start the openvla pretrained basic model

1. Run the Docker container using (Windows), you need an NVIDIA GPU:
   ´´´
   docker run -it  --name my-app-container --gpus all  -v "${pwd}:/app/Mounted_Repo" my-project-env bash
    ´´´

2. Go to the folder /app/Mounted_Repo and run:
   ```
   python3 openvla_old.py
   ```

This runs an older demonstration version of openvla with the image of my headphones and a cup. For integration with the simulation environment, run the file ``` openvlatest.py``` 
