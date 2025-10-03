"""
This script demonstrates how to adapt a robosuite environment to be
compatible with the Gymnasium API and control it with a pre-trained
LeRobot policy (SmolVLA).

This is an extension of the original script that used random actions.
Instead of `env.action_space.sample()`, we now load the SmolVLA policy
from the Hugging Face Hub and use it to select actions based on visual
observations and a language instruction.

Key changes:
1.  Enabled camera observations in the robosuite environment, as SmolVLA
    is a vision-language-action model.
2.  Added dependencies for `lerobot`, `torch`, and `huggingface_hub`.
3.  Loaded the pre-trained `lerobot/smolvla_lift` policy.
4.  In the simulation loop, the agent's observation is processed and fed
    to the policy to get a meaningful action.
"""

import robosuite as suite
import torch
from robosuite.wrappers import GymWrapper

# LeRobot imports for loading the policy and processing observations
from lerobot.common.policies.act.modeling_act import ACTPolicy
from lerobot.common.utils.utils import get_obs_from_gym_obs


def run_smolvla_on_robosuite():
    """
    Initializes a robosuite environment, loads the SmolVLA policy,
    and runs a few episodes of the "Lift" task.
    """
    # 1. Set up the device to run the policy on (e.g., "cuda" or "cpu")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # 2. Load the SmolVLA policy from the Hugging Face Hub.
    # This policy is pre-trained on the "Lift" task.
    policy = ACTPolicy.from_pretrained("lerobot/smolvla_lift", device=device)
    print("SmolVLA policy loaded successfully.")

    # 3. Create the robosuite environment.
    # Notice the changes to enable vision for the SmolVLA model.
    env = GymWrapper(
        suite.make(
            "Lift",
            robots="Panda",  # SmolVLA was trained with Panda
            use_camera_obs=True,  # Use pixel observations for the policy
            has_offscreen_renderer=True,  # Required for camera observations
            has_renderer=True,  # Make sure we can render to the screen
            reward_shaping=True,  # Use dense rewards
            control_freq=20,  # Control frequency
            camera_names="agentview",  # Specify the camera to use
            camera_heights=84,  # Image height matching policy's training
            camera_widths=84,  # Image width matching policy's training
            hard_reset=False, # Smoother resets
        )
    )

    # 4. Run a few episodes
    for i_episode in range(5):
        print(f"--- Starting Episode: {i_episode + 1} ---")
        # Reset the environment and get the initial observation dictionary
        gym_obs, info = env.reset()

        # The task instruction for the VLA model
        instruction = "lift the cube"

        for t in range(500):
            env.render()

            # Prepare the observation for the policy.
            # This utility function from LeRobot formats the gym observation
            # dictionary into the structure the policy expects.
            obs = get_obs_from_gym_obs(gym_obs, ["agentview_image"], instruction)

            # Get the action from the SmolVLA policy
            with torch.no_grad():
                action = policy.select_action(obs)

            # Take a step in the environment with the policy's action
            gym_obs, reward, terminated, truncated, info = env.step(action)

            if terminated or truncated:
                print(f"Episode finished after {t + 1} timesteps.")
                break

    env.close()
    print("--- Simulation Finished ---")


if __name__ == "__main__":
    run_smolvla_on_robosuite()
