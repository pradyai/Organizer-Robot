from transformers import AutoModelForVision2Seq, AutoProcessor
from PIL import Image
import cv2
import torch

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

# Convert BGR (OpenCV) to RGB (PIL)
frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
image = Image.fromarray(frame_rgb)

# Prompt (insert real instruction)
print("Processing input...")
instruction = "pick up the black headphones"
prompt = f"In: What action should the robot take to {instruction}?\nOut:"

# Process input and predict action
inputs = processor(prompt, image).to("cuda:0", dtype=torch.float16)
action = vla.predict_action(**inputs, unnorm_key="bridge_orig", do_sample=False)

# Output
print("Predicted action:", action)
