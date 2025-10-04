import torch
import time
from dataclasses import dataclass
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from transformers import AutoProcessor

# Dummy TimedObservation class
@dataclass
class TimedObservation:
    timestamp: float
    observation: dict
    timestep: int
    must_go: bool = True

# Load model (replace with your checkpoint if needed)
policy = SmolVLAPolicy.from_pretrained("outputs/train/example_smolvla").to("cpu")
policy.eval()

# Patch missing language tokenizer
policy.language_tokenizer = AutoProcessor.from_pretrained(policy.config.vlm_model_name).tokenizer

# Batch configuration
batch_size = 1
img_shape = (3, 512, 512)  # (C, H, W)
state_dim = 6  # so100 joint positions

# Create dummy TimedObservation
dummy_obs = TimedObservation(
    timestamp=time.time(),
    observation={
        "observation.images.top": torch.rand(batch_size, *img_shape, device="cpu"),
        "observation.images.side": torch.rand(batch_size, *img_shape, device="cpu"),  # kept in dict but ignored
        "observation.state": torch.rand(batch_size, state_dim, device="cpu"),
        "task": ["stack the blocks"] * batch_size
    },
    timestep=0,
)

# --- Prepare inputs for the model ---
normalized_batch = policy.normalize_inputs(dummy_obs.observation)
images, img_masks = policy.prepare_images(normalized_batch)  # only top images
state = policy.prepare_state(normalized_batch)
lang_tokens, lang_masks = policy.prepare_language(normalized_batch)

# Warmup
for _ in range(3):
    with torch.no_grad():
        _ = policy.model.sample_actions(images, img_masks, lang_tokens, lang_masks, state)

# Inference
start_time = time.perf_counter()
with torch.no_grad():
    actions = policy.model.sample_actions(images, img_masks, lang_tokens, lang_masks, state)
end_time = time.perf_counter()

print(f"Actions shape: {actions.shape}")
print(actions)
print(f"Inference time: {end_time - start_time:.4f} s")
