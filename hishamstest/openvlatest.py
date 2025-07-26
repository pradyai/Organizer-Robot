from transformers import AutoModelForVision2Seq, AutoProcessor
from PIL import Image
import cv2
import torch
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

def SendPosToRobot(dSetpointVector):
    # Placeholder function to send position to robot
    # Implement the actual logic to send the setpoint vector to your robot
    #needs inverse dynamics
    return

# Load model & processor
# pip install transformers==4.41.2 --force-reinstall --no-cache-dir  

print("Loading model and processor...")
processor = AutoProcessor.from_pretrained("openvla/openvla-7b", trust_remote_code=True)
vla = AutoModelForVision2Seq.from_pretrained(
    "openvla/openvla-7b", 
    attn_implementation=None,  # [Optional] Requires `flash_attn`
    torch_dtype=torch.bfloat16, 
    low_cpu_mem_usage=True, 
    trust_remote_code=True
).to("cuda:0")

instruction = "pick up the white cup"

bSetpointReached = False #variable to control the loop
dSetpointVector = None #variable to store the setpoint vector

while True:

    if bSetpointReached == True:
        pil_img = Image.open("frame_plot.jpg").convert("RGB") # REPLACE WITH YOUR VIDEO SOURCE

        # Convert PIL Image to NumPy array (RGB)
        frame_rgb = np.array(pil_img)

        # If you need OpenCV BGR format instead of RGB:
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        # Now frame_rgb or frame_bgr is usable like a frame from cv2.VideoCapture

        # Convert BGR (OpenCV) to RGB (PIL)
        image = Image.fromarray(frame_rgb)

        # Prompt (insert real instruction)
        print("Processing input...")
        prompt = f"In: What action should the robot take to {instruction}?\nOut:"

        # Process input and predict action
        inputs = processor(prompt, image).to("cuda:0", dtype=torch.bfloat16)
        dSetpointVector = vla.predict_action(**inputs, unnorm_key="bridge_orig", do_sample=False)
        
        SendPosToRobot(dSetpointVector) #IMPLEMENT THIS FUNCTION, its a function to send the setpoint vector to the robot

        # Output
        print("The action for the given prompt is:")
        print("Predicted action:", dSetpointVector)
        
    else: #if the setpoint is not reached, do nothing, the robot is still moving
        bSetpointReached = False
        
        dRobot_position = None # Replace with actual robot position retrieval logicq
        
        if dRobot_position == dSetpointVector:
            setpoint_reached = True
        continue
