#!/usr/bin/env python3
"""
Teleoperation Data Recorder for Robosuite

Records joint positions and camera images during keyboard teleoperation
and publishes formatted data to terminal at each timestep.
"""

import argparse
import time
import json
import numpy as np
import robosuite as suite
from robosuite import load_composite_controller_config
from robosuite.controllers.composite.composite_controller import WholeBody
from robosuite.wrappers import VisualizationWrapper
from robosuite.utils.input_utils import *
from copy import deepcopy
import pickle
import datetime
import os
from PIL import Image
import cv2

class TeleopDataRecorder:
    def __init__(self, env_name="Lift", robot="Panda", camera_names=None, record_freq=1.0):
        """
        Initialize the teleoperation data recorder.
        
        Args:
            env_name: Robosuite environment name
            robot: Robot type to use
            camera_names: List of camera names to record (None for auto-detect)
            record_freq: Recording frequency in Hz (default 1.0 for per-second recording)
        """
        self.env_name = env_name
        self.robot_name = robot
        
        # Auto-detect cameras based on robot if not specified
        if camera_names is None:
            if robot == "Panda":
                self.camera_names = ["agentview"]  # Panda typically only has agentview
            else:
                self.camera_names = ["agentview", "robot0_eye_in_hand"]
        else:
            self.camera_names = camera_names
            
        self.record_freq = record_freq
        self.record_interval = 1.0 / record_freq  # Time between recordings
        self.last_record_time = 0
        
        # Create data directories
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_dir = f"smolvla_data_{self.session_id}"
        self.images_dir = os.path.join(self.data_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(os.path.join(self.images_dir, "top"), exist_ok=True)
        os.makedirs(os.path.join(self.images_dir, "wrist"), exist_ok=True)
        
        # Joint name mappings for different robots
        self.joint_mappings = {
            "Panda": {
                "shoulder_pan": 0,      # panda_joint1
                "shoulder_lift": 1,     # panda_joint2  
                "elbow_flex": 2,        # panda_joint3
                "wrist_flex": 3,        # panda_joint4
                "wrist_roll": 4,        # panda_joint5
                "gripper": "gripper"    # gripper position
            },
            "SO101": {
                "shoulder_pan": 0,
                "shoulder_lift": 1,
                "elbow_flex": 2,
                "wrist_flex": 3,
                "wrist_roll": 4,
                "gripper": "gripper"
            }
        }
        
        # Camera name mappings - let's check what's actually available
        self.camera_mappings = {
            "top": "agentview",
            "wrist": "robot0_eye_in_hand"  # This might not exist for Panda
        }
        
        self.setup_environment()
        
    def setup_environment(self):
        """Setup the robosuite environment."""
        print(f"Setting up {self.env_name} environment with {self.robot_name} robot...")
        
        # Load controller configuration
        controller_config = load_composite_controller_config(
            controller=None, 
            robot=self.robot_name
        )
        
        # Create environment
        self.env = suite.make(
            self.env_name,
            robots=self.robot_name,
            has_renderer=True,
            has_offscreen_renderer=True,
            ignore_done=True,
            use_camera_obs=True,
            camera_names=self.camera_names,
            camera_heights=224,  # Standard size for VLA models
            camera_widths=224,
            control_freq=20,
            controller_configs=controller_config,
        )
        
        # Wrap with visualization
        self.env = VisualizationWrapper(self.env, indicator_configs=None)
        
        # Setup device
        from robosuite.devices import Keyboard
        self.device = Keyboard(
            env=self.env, 
            pos_sensitivity=1.5, 
            rot_sensitivity=1.5
        )
        
        # Add keyboard callbacks
        self.env.viewer.add_keypress_callback(self.device.on_press)
        
        print("Environment setup complete!")
        print("\nControls:")
        print("Arrow keys: Move horizontally")
        print(".,; keys: Move vertically") 
        print("o-p: Rotate (yaw)")
        print("y-h: Rotate (pitch)")
        print("e-r: Rotate (roll)")
        print("Spacebar: Toggle gripper")
        print("Ctrl+Q: Reset and save data")
        print("-" * 50)

    def get_joint_positions(self, obs):
        """Extract joint positions from observation."""
        joint_mapping = self.joint_mappings.get(self.robot_name, {})
        joint_data = {}
        
        # Get joint positions array
        joint_pos = obs.get("robot0_joint_pos", np.zeros(7))
        
        # Debug: Print available observation keys first time
        if not hasattr(self, '_debug_printed'):
            print(f"\nDEBUG: Available observation keys: {list(obs.keys())}")
            print(f"DEBUG: Joint positions shape: {joint_pos.shape if hasattr(joint_pos, 'shape') else 'N/A'}")
            print(f"DEBUG: Joint positions: {joint_pos}")
            if "robot0_gripper_qpos" in obs:
                print(f"DEBUG: Gripper pos: {obs['robot0_gripper_qpos']}")
            self._debug_printed = True
        
        for joint_name, joint_idx in joint_mapping.items():
            if joint_name == "gripper":
                # Get gripper position
                gripper_pos = obs.get("robot0_gripper_qpos", np.array([0.0]))
                if hasattr(gripper_pos, '__len__') and len(gripper_pos) > 0:
                    joint_data[f"{joint_name}.pos"] = float(gripper_pos[0])
                else:
                    joint_data[f"{joint_name}.pos"] = float(gripper_pos)
            else:
                # Regular joint positions
                if joint_idx < len(joint_pos):
                    joint_data[f"{joint_name}.pos"] = float(joint_pos[joint_idx])
                else:
                    joint_data[f"{joint_name}.pos"] = 0.0
                    
        return joint_data

    def get_camera_images(self, obs):
        """Extract camera images from observation."""
        image_data = {}
        
        # Debug: Print available camera keys first time
        if not hasattr(self, '_camera_debug_printed'):
            camera_keys = [k for k in obs.keys() if 'image' in k.lower()]
            print(f"DEBUG: Available camera keys: {camera_keys}")
            self._camera_debug_printed = True
        
        for display_name, camera_name in self.camera_mappings.items():
            image_key = f"{camera_name}_image"
            if image_key in obs:
                # Convert to uint8 if needed
                image = obs[image_key]
                if image.dtype != np.uint8:
                    image = (image * 255).astype(np.uint8)
                image_data[f"images.{display_name}"] = image
                print(f"DEBUG: Captured {display_name} image with shape {image.shape}")
            else:
                # Try alternative camera names
                if display_name == "wrist":
                    # Try other possible wrist camera names
                    alt_names = ["frontview", "robot0_robotiq_2f_85_eye_in_hand", "sideview"]
                    found = False
                    for alt_name in alt_names:
                        alt_key = f"{alt_name}_image"
                        if alt_key in obs:
                            image = obs[alt_key]
                            if image.dtype != np.uint8:
                                image = (image * 255).astype(np.uint8)
                            image_data[f"images.{display_name}"] = image
                            print(f"DEBUG: Using {alt_name} for wrist camera")
                            found = True
                            break
                    if not found:
                        print(f"DEBUG: No wrist camera found, using placeholder")
                        image_data[f"images.{display_name}"] = np.zeros((224, 224, 3), dtype=np.uint8)
                else:
                    print(f"DEBUG: Camera {camera_name} not found, using placeholder")
                    image_data[f"images.{display_name}"] = np.zeros((224, 224, 3), dtype=np.uint8)
                
        return image_data

    def format_data_for_display(self, joint_data, image_data, timestep):
        """Format data for terminal display."""
        data = {**joint_data, **image_data}
        
        # Create a display-friendly version
        display_data = {}
        for key, value in data.items():
            if isinstance(value, np.ndarray):
                if value.size > 10:  # Image arrays
                    display_data[key] = f"np.array(shape={value.shape}, dtype={value.dtype})"
                else:
                    display_data[key] = value.tolist()
            else:
                display_data[key] = round(float(value), 3)
        
        return data, display_data

    def save_images(self, image_data, second_count):
        """Save images to disk for the current second."""
        for key, image in image_data.items():
            if isinstance(image, np.ndarray) and image.size > 10:  # Only save actual images
                # Extract camera type from key (e.g., "images.top" -> "top")
                camera_type = key.split(".")[-1]
                filename = f"{camera_type}_{second_count:04d}.jpg"
                filepath = os.path.join(self.images_dir, camera_type, filename)
                
                # Convert RGB to BGR for OpenCV
                if len(image.shape) == 3 and image.shape[2] == 3:
                    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(filepath, image_bgr)

    def run_teleoperation(self):
        """Main teleoperation loop."""
        print("Starting teleoperation data recording...")
        
        episode_data = []
        timestep = 0
        
        while True:
            obs = self.env.reset()
            self.env.render()
            
            # Reset recording timer for new episode
            self.last_record_time = time.time()
            
            # Initialize control variables
            self.device.start_control()
            
            all_prev_gripper_actions = [
                {
                    f"{robot_arm}_gripper": np.repeat([0], robot.gripper[robot_arm].dof)
                    for robot_arm in robot.arms
                    if robot.gripper[robot_arm].dof > 0
                }
                for robot in self.env.robots
            ]
            
            print(f"\n=== Episode Started ===")
            timestep = 0
            
            while True:
                start_time = time.time()
                timestep += 1
                
                # Set active robot
                active_robot = self.env.robots[self.device.active_robot]
                
                # Get action from device
                input_ac_dict = self.device.input2action()
                
                # Check for reset
                if input_ac_dict is None:
                    print(f"\n=== Episode Reset (recorded {len(episode_data)} seconds) ===")
                    if episode_data:
                        self.save_episode_data(episode_data)
                    break
                
                # Process actions
                action_dict = deepcopy(input_ac_dict)
                
                # Set arm actions
                for arm in active_robot.arms:
                    if isinstance(active_robot.composite_controller, WholeBody):
                        controller_input_type = active_robot.composite_controller.joint_action_policy.input_type
                    else:
                        controller_input_type = active_robot.part_controllers[arm].input_type

                    if controller_input_type == "delta":
                        action_dict[arm] = input_ac_dict[f"{arm}_delta"]
                    elif controller_input_type == "absolute":
                        action_dict[arm] = input_ac_dict[f"{arm}_abs"]
                    else:
                        raise ValueError("Unknown controller input type")

                # Create environment action
                env_action = [robot.create_action_vector(all_prev_gripper_actions[i]) for i, robot in enumerate(self.env.robots)]
                env_action[self.device.active_robot] = active_robot.create_action_vector(action_dict)
                env_action = np.concatenate(env_action)
                
                # Update gripper actions
                for gripper_ac in all_prev_gripper_actions[self.device.active_robot]:
                    all_prev_gripper_actions[self.device.active_robot][gripper_ac] = action_dict[gripper_ac]

                # Step environment
                obs, reward, done, info = self.env.step(env_action)
                
                # Check if it's time to record (once per second)
                current_time = time.time()
                if current_time - self.last_record_time >= self.record_interval:
                    # Record data
                    joint_data = self.get_joint_positions(obs)
                    image_data = self.get_camera_images(obs)
                    
                    # Format for display and storage
                    full_data, display_data = self.format_data_for_display(joint_data, image_data, timestep)
                    
                    # Print to terminal
                    print(f"\n--- Second {len(episode_data) + 1} (Timestep {timestep}) ---")
                    print(json.dumps(display_data, indent=2))
                    
                    # Store full data
                    episode_data.append({
                        "timestep": timestep,
                        "joint_positions": joint_data,
                        "images": {k: v for k, v in image_data.items()},
                        "action": env_action.tolist(),
                        "timestamp": current_time
                    })
                    
                    # Save images to disk for this second
                    self.save_images(image_data, len(episode_data))
                    
                    # Update last record time
                    self.last_record_time = current_time
                
                # Render
                self.env.render()
                
                # Maintain framerate
                elapsed = time.time() - start_time
                sleep_time = 1/20 - elapsed  # 20 FPS
                if sleep_time > 0:
                    time.sleep(sleep_time)

    def save_episode_data(self, episode_data):
        """Save recorded episode data in smolVLA format."""
        if not episode_data:
            return
            
        # Create JSON file with episode metadata and joint positions
        metadata = {
            "episode_info": {
                "robot": self.robot_name,
                "environment": self.env_name,
                "session_id": self.session_id,
                "num_seconds": len(episode_data),
                "recording_frequency": self.record_freq
            },
            "data": []
        }
        
        for i, data_point in enumerate(episode_data):
            # Create entry for this second
            entry = {
                "second": i + 1,
                "timestep": data_point["timestep"],
                "joint_positions": data_point["joint_positions"],
                "action": data_point["action"],
                "timestamp": data_point["timestamp"],
                "image_files": {
                    "top": f"images/top/top_{i+1:04d}.jpg",
                    "wrist": f"images/wrist/wrist_{i+1:04d}.jpg"
                }
            }
            metadata["data"].append(entry)
        
        # Save metadata JSON
        json_filename = os.path.join(self.data_dir, "episode_data.json")
        with open(json_filename, "w") as f:
            json.dump(metadata, f, indent=2)
            
        # Also save as pickle for compatibility
        pkl_filename = os.path.join(self.data_dir, "episode_data.pkl")
        with open(pkl_filename, "wb") as f:
            pickle.dump(episode_data, f)
            
        print(f"\n=== Episode Data Saved ===")
        print(f"Dataset directory: {self.data_dir}")
        print(f"JSON metadata: {json_filename}")
        print(f"Pickle data: {pkl_filename}")
        print(f"Images saved in: {self.images_dir}")
        print(f"Total seconds recorded: {len(episode_data)}")
        print("Dataset ready for smolVLA training!")

def main():
    parser = argparse.ArgumentParser(description="Teleoperation Data Recorder")
    parser.add_argument("--environment", type=str, default="Lift", 
                       help="Robosuite environment")
    parser.add_argument("--robot", type=str, default="Panda",
                       help="Robot to use")
    parser.add_argument("--cameras", nargs="+", default=["agentview", "robot0_eye_in_hand"],
                       help="Camera names to record")
    
    args = parser.parse_args()
    
    # Create recorder
    recorder = TeleopDataRecorder(
        env_name=args.environment,
        robot=args.robot, 
        camera_names=args.cameras
    )
    
    try:
        # Start recording
        recorder.run_teleoperation()
    except KeyboardInterrupt:
        print("\nTeleoperation stopped by user")
    except Exception as e:
        print(f"Error during teleoperation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()