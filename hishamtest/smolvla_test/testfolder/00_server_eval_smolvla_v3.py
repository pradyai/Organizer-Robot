import socket
import pickle
import torch
from dataclasses import dataclass
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from transformers import AutoProcessor
from lerobot.scripts.server.helpers import TimedObservation
import time

HOST = "127.0.0.1"
PORT = 6006


# Load policy
policy = SmolVLAPolicy.from_pretrained("outputs/train/example_smolvla").to("cpu")
policy.eval()
policy.language_tokenizer = AutoProcessor.from_pretrained(policy.config.vlm_model_name).tokenizer

print(f"[Server] Listening on {HOST}:{PORT}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    while True:
        conn, addr = s.accept()
        with conn:
            print(f"[Server] Connected by {addr}")
            try:
                while True:
                    # Read message length
                    raw_len = conn.recv(4)
                    if not raw_len:
                        print("[Server] Connection closed by client")
                        break
                    msg_len = int.from_bytes(raw_len, "big")

                    # Read the full message
                    data = b""
                    while len(data) < msg_len:
                        packet = conn.recv(msg_len - len(data))
                        if not packet:
                            break
                        data += packet

                    if not data:
                        print("[Server] No data received. Closing connection.")
                        break

                    # Deserialize TimedObservation
                    timed_obs: TimedObservation = pickle.loads(data)

                    # Convert observation fields to torch tensors
                    obs_dict = timed_obs.observation
                    obs_dict["observation.images.top"] = obs_dict["observation.images.top"].float()
                    obs_dict["observation.images.wrist"] = obs_dict["observation.images.wrist"].float()
                    obs_dict["observation.state"] = obs_dict["observation.state"].float()
                    
                    obs_dict["task"] = ["stack the blocks"]  # empty instruction


                    # --- Prepare inputs for the model ---
                    normalized_batch = policy.normalize_inputs(obs_dict)
                    images, img_masks = policy.prepare_images(normalized_batch)
                    state = policy.prepare_state(normalized_batch)
                    lang_tokens, lang_masks = policy.prepare_language(normalized_batch)
                    # ---

                    # Sample actions
                    start_time = time.perf_counter()
                    with torch.no_grad():
                        actions = policy.model.sample_actions(images, img_masks, lang_tokens, lang_masks, state)
                    end_time = time.perf_counter()

                    print(f"[Server] Inference for timestep {timed_obs.timestep} took {end_time - start_time:.4f}s")

                    # Serialize and send back
                    actions_bytes = pickle.dumps(actions)
                    conn.sendall(len(actions_bytes).to_bytes(4, "big") + actions_bytes)

            except Exception as e:
                print(f"[Server] Error: {e}")
            finally:
                print("[Server] Client disconnected")
