#!/usr/bin/env python3
"""
Simple Teleoperation Data Recorder for smolVLA

Records joint positions and camera images at 1Hz during keyboard teleoperation.
Saves data in format suitable for smolVLA training.
"""

import argparse
import time
import json
import numpy as np
import robosuite as suite
from robosuite import load_composite_controller_config
from robosuite.wrappers import VisualizationWrapper
from copy import deepcopy
import pickle
import datetime
import os
from PIL import Image

def setup_environment(env_name="Lift", robot="Panda"):
    """Setup the robosuite environment."""
    print(f"Setting up {env_name} environment with {robot} robot...")
    
    # Load controller configuration
    controller_config = load_composite_controller_config(controller=None, robot=robot)
    
    # Create environment
    env = suite.make(
        env_name,
        robots=robot,
        has_renderer=True,
        has_offscreen_renderer=True,
        ignore_done=True,
        use_camera_obs=True,
        camera_names=["agentview", "robot0_eye_in_hand"],
        camera_heights=224,
        camera_widths=224,
        control_freq=20,
        controller_configs=controller_config,
    )
    
    # Wrap with visualization
    env = VisualizationWrapper(env, indicator_configs=None)
    
    # Setup keyboard device
    from robosuite.devices import Keyboard
    device = Keyboard(env=env, pos_sensitivity=1.5, rot_sensitivity=1.5)
    env.viewer.add_keypress_callback(device.on_press)
    
    return env, device

def get_joint_data(obs, robot_name="Panda"):
    """Extract joint positions from observation."""
    joint_data = {}
    
    # Get joint positions
    joint_pos = obs.get("robot0_joint_pos", np.zeros(7))
    gripper_pos = obs.get("robot0_gripper_qpos", [0.0])
    
    # Map to named joints
    joint_data["shoulder_pan.pos"] = float(joint_pos[0]) if len(joint_pos) > 0 else 0.0
    joint_data["shoulder_lift.pos"] = float(joint_pos[1]) if len(joint_pos) > 1 else 0.0
    joint_data["elbow_flex.pos"] = float(joint_pos[2]) if len(joint_pos) > 2 else 0.0
    joint_data["wrist_flex.pos"] = float(joint_pos[3]) if len(joint_pos) > 3 else 0.0
    joint_data["wrist_roll.pos"] = float(joint_pos[4]) if len(joint_pos) > 4 else 0.0
    joint_data["gripper.pos"] = float(gripper_pos[0]) if hasattr(gripper_pos, '__len__') else float(gripper_pos)
    
    return joint_data

def save_images_and_get_paths(obs, timestep, images_dir):
    """Save camera images and return file paths."""
    image_paths = {}
    
    # Top camera (agentview)
    if "agentview_image" in obs:
        image = obs["agentview_image"]
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)
        
        top_path = os.path.join(images_dir, "top", f"step_{timestep:06d}.jpg")
        Image.fromarray(image).save(top_path, quality=95)
        image_paths["images.top"] = image
        image_paths["images.top_path"] = top_path
    else:
        image_paths["images.top"] = np.zeros((224, 224, 3), dtype=np.uint8)
        image_paths["images.top_path"] = None
    
    # Wrist camera
    if "robot0_eye_in_hand_image" in obs:
        image = obs["robot0_eye_in_hand_image"]
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)
        
        wrist_path = os.path.join(images_dir, "wrist", f"step_{timestep:06d}.jpg")
        Image.fromarray(image).save(wrist_path, quality=95)
        image_paths["images.wrist"] = image
        image_paths["images.wrist_path"] = wrist_path
    else:
        image_paths["images.wrist"] = np.zeros((224, 224, 3), dtype=np.uint8)
        image_paths["images.wrist_path"] = None
    
    return image_paths

def main():
    parser = argparse.ArgumentParser(description="Simple Teleoperation Data Recorder")
    parser.add_argument("--environment", type=str, default="Lift", help="Environment name")
    parser.add_argument("--robot", type=str, default="Panda", help="Robot name")
    parser.add_argument("--record-freq", type=float, default=1.0, help="Recording frequency (Hz)")
    
    args = parser.parse_args()
    
    # Setup data directories
    session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    data_dir = f"smolvla_data_{session_id}"
    images_dir = os.path.join(data_dir, "images")
    os.makedirs(os.path.join(images_dir, "top"), exist_ok=True)
    os.makedirs(os.path.join(images_dir, "wrist"), exist_ok=True)
    
    # Setup environment
    env, device = setup_environment(args.environment, args.robot)
    
    print("\\nControls:")
    print("Arrow keys: Move horizontally")
    print(".,; keys: Move vertically")
    print("o-p: Rotate (yaw)")
    print("y-h: Rotate (pitch)")
    print("e-r: Rotate (roll)")
    print("Spacebar: Toggle gripper")
    print("Ctrl+Q: Reset and save data")
    print(f"Recording at {args.record_freq} Hz")
    print("-" * 50)
    
    record_interval = 1.0 / args.record_freq
    last_record_time = 0
    episode_data = []
    recorded_timestep = 0
    
    try:
        while True:
            obs = env.reset()
            env.render()
            device.start_control()
            
            print(f"\\n=== Episode Started ===")
            
            # Initialize gripper actions
            all_prev_gripper_actions = [{
                f"{robot_arm}_gripper": np.repeat([0], robot.gripper[robot_arm].dof)
                for robot_arm in robot.arms
                if robot.gripper[robot_arm].dof > 0
            } for robot in env.robots]
            
            while True:
                start_time = time.time()
                
                # Get action from keyboard
                input_ac_dict = device.input2action()
                
                # Check for reset
                if input_ac_dict is None:
                    print(f"\\n=== Episode Reset (recorded {recorded_timestep} timesteps) ===")
                    if episode_data:
                        # Save episode data
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        pkl_file = os.path.join(data_dir, f"episode_{timestamp}.pkl")
                        
                        with open(pkl_file, "wb") as f:
                            pickle.dump(episode_data, f)
                        
                        print(f"Saved {len(episode_data)} timesteps to {pkl_file}")
                        episode_data = []
                        recorded_timestep = 0
                    break
                
                # Process actions (simplified)
                active_robot = env.robots[device.active_robot]
                action_dict = deepcopy(input_ac_dict)
                
                # Set arm actions
                for arm in active_robot.arms:
                    controller_input_type = getattr(active_robot.part_controllers[arm], 'input_type', 'delta')
                    if controller_input_type == "delta":
                        action_dict[arm] = input_ac_dict[f"{arm}_delta"]
                    elif controller_input_type == "absolute":
                        action_dict[arm] = input_ac_dict[f"{arm}_abs"]
                
                # Create environment action
                env_action = [robot.create_action_vector(all_prev_gripper_actions[i]) for i, robot in enumerate(env.robots)]
                env_action[device.active_robot] = active_robot.create_action_vector(action_dict)
                env_action = np.concatenate(env_action)
                
                # Update gripper state
                for gripper_ac in all_prev_gripper_actions[device.active_robot]:
                    all_prev_gripper_actions[device.active_robot][gripper_ac] = action_dict[gripper_ac]
                
                # Step environment
                obs, reward, done, info = env.step(env_action)
                env.render()
                
                # Record data at specified frequency
                current_time = time.time()
                if current_time - last_record_time >= record_interval:
                    recorded_timestep += 1
                    
                    # Get joint positions
                    joint_data = get_joint_data(obs, args.robot)
                    
                    # Save images and get paths
                    image_data = save_images_and_get_paths(obs, recorded_timestep, images_dir)
                    
                    # Combine data in the requested format
                    timestep_data = {
                        **joint_data,
                        **{k: v for k, v in image_data.items() if not k.endswith('_path')}
                    }
                    
                    # Print to terminal
                    print(f"\\n--- Timestep {recorded_timestep} ({current_time:.2f}s) ---")
                    display_data = {}
                    for key, value in timestep_data.items():
                        if isinstance(value, np.ndarray):
                            display_data[key] = f"shape={value.shape}, dtype={value.dtype}"
                        else:
                            display_data[key] = round(float(value), 3)
                    print(json.dumps(display_data, indent=2))
                    
                    # Store for training
                    episode_data.append({
                        "timestep": recorded_timestep,
                        "joint_positions": joint_data,
                        "image_paths": {k: v for k, v in image_data.items() if k.endswith('_path')},
                        "images": {k: v for k, v in image_data.items() if not k.endswith('_path')},
                        "action": env_action.tolist(),
                        "timestamp": current_time,
                        "language_instruction": f"Perform {args.environment.lower()} task"
                    })
                    
                    last_record_time = current_time
                
                # Maintain simulation framerate
                elapsed = time.time() - start_time
                sleep_time = 1/20 - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        print("\\nStopped by user")
        if episode_data:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            pkl_file = os.path.join(data_dir, f"episode_{timestamp}.pkl")
            with open(pkl_file, "wb") as f:
                pickle.dump(episode_data, f)
            print(f"Saved final {len(episode_data)} timesteps to {pkl_file}")

if __name__ == "__main__":
    main()