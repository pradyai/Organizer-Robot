import torch
import time
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
from transformers import AutoProcessor
import socket
import json
 
# Load model (replace with your checkpoint if needed)
policy = SmolVLAPolicy.from_pretrained("outputs/train/example_smolvla").to("cpu")
policy.eval()
 
 
 
# patch: The loaded policy is missing the language_tokenizer attribute.
policy.language_tokenizer = AutoProcessor.from_pretrained(policy.config.vlm_model_name).tokenizer
 
# Dummy batch config for a single observation
batch_size = 1
img_shape = (3, 512, 512)  # (C, H, W)
# Infer state_dim from the loaded normalization stats
state_dim = policy.normalize_inputs.buffer_observation_state.mean.shape[-1]
 
dummy_batch = {
    # a single image observation
    "observation.images.top": torch.rand(batch_size, *img_shape, device="cpu"),
    # a single state observation
    "observation.state": torch.rand(batch_size, state_dim, device="cpu"),
    "task": ["stack the blocks"] * batch_size,
}
 
# --- Prepare inputs for the model ---
# The policy expects normalized inputs and specific data preparation.
normalized_batch = policy.normalize_inputs(dummy_batch)
images, img_masks = policy.prepare_images(normalized_batch)
state = policy.prepare_state(normalized_batch)
lang_tokens, lang_masks = policy.prepare_language(normalized_batch)
# ---

# Warmup
for _ in range(3):
    with torch.no_grad():
        _ = policy.model.sample_actions(images, img_masks, lang_tokens, lang_masks, state)
 
 #socket implementation
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 5005       # Choose any free port

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
print(f"Server listening on {HOST}:{PORT}")
 
conn, addr = server_socket.accept()
print(f"Connected by {addr}")

try:
    while True:
        # --- Generate actions ---
        with torch.no_grad():
            actions = policy.model.sample_actions(
                images, img_masks, lang_tokens, lang_masks, state
            )


        print(actions)
        # Convert tensor to Python list
        actions_list = actions.cpu().numpy().tolist()

        # Serialize to JSON
        msg = json.dumps({"actions": actions_list})

        # Send length prefix first (optional but good practice)
        msg_bytes = msg.encode("utf-8")
        msg_len = len(msg_bytes)
        conn.sendall(msg_len.to_bytes(4, "big") + msg_bytes)

        # Send at a fixed timestep
        time.sleep(10)  # 50 ms = 20 Hz
finally:
    conn.close()
    server_socket.close()