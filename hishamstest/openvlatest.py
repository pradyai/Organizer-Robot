from transformers import AutoModelForVision2Seq, AutoProcessor
from PIL import Image
import cv2
import torch
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

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

'''
# Capture a single frame from webcam
print("Capturing image from webcam...")
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
cap.release()

if not ret:
    raise RuntimeError("Failed to capture image from webcam")

print("Image captured successfully.")
# Show the frame (OpenCV window)
cv2.imshow("Captured Frame", frame)
cv2.waitKey(0)  # Press any key to close the window
cv2.destroyAllWindows()

stream_url = "http://host.docker.internal:8080"

cap = cv2.VideoCapture(stream_url)
ret, frame = cap.read()
if ret:
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    plt.imshow(frame_rgb)
    plt.axis('off')
    plt.savefig("frame_plot.png")
    print("Saved frame plot as frame_plot.png")
else:
    print("Failed to read frame")

cap.release()

'''

pil_img = Image.open("frame_plot.png").convert("RGB")

# Convert PIL Image to NumPy array (RGB)
frame_rgb = np.array(pil_img)

# If you need OpenCV BGR format instead of RGB:
frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

# Now frame_rgb or frame_bgr is usable like a frame from cv2.VideoCapture

# Convert BGR (OpenCV) to RGB (PIL)
image = Image.fromarray(frame_rgb)

# Prompt (insert real instruction)
print("Processing input...")
instruction = "pick up the tshirt"
prompt = f"In: What action should the robot take to {instruction}?\nOut:"

# Process input and predict action
inputs = processor(prompt, image).to("cuda:0", dtype=torch.bfloat16)
action = vla.predict_action(**inputs, unnorm_key="bridge_orig", do_sample=False)

# Output
print("Predicted action:", action)
