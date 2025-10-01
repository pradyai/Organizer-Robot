import torch
import time
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
from transformers import AutoProcessor
 
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
 
# Benchmark
#torch.cuda.reset_peak_memory_stats()
with torch.no_grad():
    actions = policy.model.sample_actions(images, img_masks, lang_tokens, lang_masks, state)
print(actions.shape)
print(actions)

 
#Avg inference time: 0.086982 s
#Max GPU memory used: 908.43 MB