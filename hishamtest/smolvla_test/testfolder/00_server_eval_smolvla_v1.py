import socket
import pickle
import torch
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from transformers import AutoProcessor

HOST = "0.0.0.0"
PORT = 6006

# Load policy
policy = SmolVLAPolicy.from_pretrained("outputs/train/example_smolvla").to("cpu")
policy.eval()
policy.language_tokenizer = AutoProcessor.from_pretrained(policy.config.vlm_model_name).tokenizer

print(f"[Server] Listening on {HOST}:{PORT}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"[Server] Connected by {addr}")
        
        
        while True:
            # Receive message length first (4 bytes)
            raw_len = conn.recv(4)
            if not raw_len:
                print("[Server] Connection closed by client")
                break
            msg_len = int.from_bytes(raw_len, "big")

            # Receive full message
            data = b""
            while len(data) < msg_len:
                chunk = conn.recv(msg_len - len(data))
                if not chunk:
                    raise RuntimeError("Connection closed during data transfer")
                data += chunk

            # Deserialize batch
            batch = pickle.loads(data)  # contains tensors and task string

            # Prepare inputs for the model
            normalized_batch = policy.normalize_inputs(batch)
            images, img_masks = policy.prepare_images(normalized_batch)
            state = policy.prepare_state(normalized_batch)
            lang_tokens, lang_masks = policy.prepare_language(normalized_batch)

            # Run policy
            with torch.no_grad():
                actions = policy.model.sample_actions(images, img_masks, lang_tokens, lang_masks, state)
                print(actions)
                print(actions.shape)

            # Send back serialized actions
            msg = pickle.dumps(actions)
            conn.sendall(len(msg).to_bytes(4, "big") + msg)
