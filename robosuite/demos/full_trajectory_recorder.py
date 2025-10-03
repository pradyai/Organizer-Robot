#!/usr/bin/env python3
"""
Full Trajectory Teleoperation Data Recorder for Robosuite

Records complete robot trajectory with joint positions and camera images 
at every timestep during keyboard teleoperation.
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

class FullTrajectoryRecorder:
    def __init__(self, env_name="Lift", robot="Panda", camera_names=None):
        """
        Initialize the full trajectory recorder.
        
        Args:
            env_name: Robosuite environment name
            robot: Robot type to use
            camera_names: List of camera names to record
        """
        self.env_name = env_name
        self.robot_name = robot
        
        # Force both cameras for complete trajectory recording
        self.camera_names = ["agentview", "robot0_eye_in_hand"]
        
        # Create data directories
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_dir = f"full_trajectory_{self.session_id}"
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
        
        # Camera name mappings
        self.camera_mappings = {
            "top": "agentview",
            "wrist": "robot0_eye_in_hand"
        }
        
        self.setup_environment()
        
    def setup_environment(self):
        """Setup the robosuite environment."""
        print(f"Setting up {self.env_name} environment with {self.robot_name} robot...")
        print("Recording FULL TRAJECTORY at 20Hz with both cameras...")
        
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
        print("Ctrl+Q: Reset and save trajectory")
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
            else:
                # Try alternative camera names for wrist camera
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
                            found = True
                            break
                    if not found:
                        # Create placeholder for missing wrist camera
                        image_data[f"images.{display_name}"] = np.zeros((224, 224, 3), dtype=np.uint8)
                else:
                    # Create placeholder for missing camera
                    image_data[f"images.{display_name}"] = np.zeros((224, 224, 3), dtype=np.uint8)
                
        return image_data

    def save_images(self, image_data, timestep):
        """Save images to disk for the current timestep."""
        for key, image in image_data.items():
            if isinstance(image, np.ndarray) and image.size > 10:  # Only save actual images
                # Extract camera type from key (e.g., "images.top" -> "top")
                camera_type = key.split(".")[-1]
                filename = f"{camera_type}_{timestep:06d}.jpg"
                filepath = os.path.join(self.images_dir, camera_type, filename)
                
                # Convert RGB to BGR for OpenCV
                if len(image.shape) == 3 and image.shape[2] == 3:
                    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(filepath, image_bgr)

    def run_teleoperation(self):
        """Main teleoperation loop - records every timestep."""
        print("Starting full trajectory recording...")
        print("Recording at 20Hz - every timestep will be captured!")
        
        episode_data = []
        
        while True:
            obs = self.env.reset()
            self.env.render()
            
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
                    print(f"\n=== Episode Reset (recorded {len(episode_data)} timesteps) ===")
                    if episode_data:
                        self.save_trajectory_data(episode_data)
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
                
                # Record data EVERY timestep
                joint_data = self.get_joint_positions(obs)
                image_data = self.get_camera_images(obs)
                
                # Create the exact format you specified
                timestep_data = {
                    **joint_data,
                    **{k: f"np.array(shape={v.shape}, dtype={v.dtype})" if isinstance(v, np.ndarray) else v 
                       for k, v in image_data.items()}
                }
                
                # Print to terminal in your specified format
                print(f"\n--- Timestep {timestep} ---")
                print(json.dumps(timestep_data, indent=2))
                
                # Store full data for saving later (with actual numpy arrays)
                episode_data.append({
                    "timestep": timestep,
                    "joint_positions": joint_data,
                    "images": image_data,  # Store actual numpy arrays
                    "action": env_action.tolist(),
                    "timestamp": time.time(),
                    # Combined format for easy access
                    "combined_data": {
                        **joint_data,
                        **image_data
                    }
                })
                
                # Save images to disk for this timestep
                self.save_images(image_data, timestep)
                
                # Render
                self.env.render()
                
                # Maintain framerate
                elapsed = time.time() - start_time
                sleep_time = 1/20 - elapsed  # 20 FPS
                if sleep_time > 0:
                    time.sleep(sleep_time)

    def save_trajectory_data(self, episode_data):
        """Save complete trajectory data."""
        if not episode_data:
            return
            
        # Create JSON file with episode metadata and full trajectory
        metadata = {
            "episode_info": {
                "robot": self.robot_name,
                "environment": self.env_name,
                "session_id": self.session_id,
                "num_timesteps": len(episode_data),
                "recording_frequency": 20.0,
                "total_duration_seconds": len(episode_data) / 20.0
            },
            "trajectory": []
        }
        
        # Save trajectory in your exact format
        for i, data_point in enumerate(episode_data):
            # Create entry for this timestep in your specified format
            entry = {
                "timestep": data_point["timestep"],
                **data_point["joint_positions"],  # Add all joint positions directly
                "images.top": f"images/top/top_{data_point['timestep']:06d}.jpg",
                "images.wrist": f"images/wrist/wrist_{data_point['timestep']:06d}.jpg",
                "action": data_point["action"],
                "timestamp": data_point["timestamp"]
            }
            metadata["trajectory"].append(entry)
        
        # Save metadata JSON
        json_filename = os.path.join(self.data_dir, "trajectory_data.json")
        with open(json_filename, "w") as f:
            json.dump(metadata, f, indent=2)
            
        # Save complete data with actual image arrays (for VLA training)
        pkl_filename = os.path.join(self.data_dir, "trajectory_complete.pkl")
        with open(pkl_filename, "wb") as f:
            pickle.dump(episode_data, f)
            
        # Create trajectory in your exact format with numpy arrays
        trajectory_exact_format = []
        for data_point in episode_data:
            formatted_point = {
                **data_point["joint_positions"],
                "images.top": data_point["images"]["images.top"],      # Actual numpy array
                "images.wrist": data_point["images"]["images.wrist"]   # Actual numpy array
            }
            trajectory_exact_format.append(formatted_point)
            
        exact_format_pkl = os.path.join(self.data_dir, "trajectory_exact_format.pkl")
        with open(exact_format_pkl, "wb") as f:
            pickle.dump(trajectory_exact_format, f)
            
        # Create a dataset summary
        summary = {
            "dataset_type": "full_trajectory",
            "format": "VLA_compatible",
            "joint_fields": list(episode_data[0]["joint_positions"].keys()),
            "image_fields": ["images.top", "images.wrist"],
            "image_shape": list(episode_data[0]["images"]["images.top"].shape),
            "total_timesteps": len(episode_data),
            "duration_seconds": len(episode_data) / 20.0,
            "recording_date": self.session_id
        }
        
        summary_filename = os.path.join(self.data_dir, "dataset_summary.json")
        with open(summary_filename, "w") as f:
            json.dump(summary, f, indent=2)
            
        print(f"\n=== Complete Trajectory Data Saved ===")
        print(f"Dataset directory: {self.data_dir}")
        print(f"JSON metadata: {json_filename}")
        print(f"Complete data: {pkl_filename}")
        print(f"Exact format: {exact_format_pkl}")
        print(f"Dataset summary: {summary_filename}")
        print(f"Images saved in: {self.images_dir}")
        print(f"Total timesteps: {len(episode_data)}")
        print(f"Duration: {len(episode_data)/20.0:.2f} seconds")
        print("Full trajectory dataset ready for VLA training!")
        
        # Show how to load the data
        print(f"\n=== How to Load the Data ===")
        print(f"# Load exact format:")
        print(f"with open('{exact_format_pkl}', 'rb') as f:")
        print(f"    trajectory = pickle.load(f)")
        print(f"# Each timestep: {list(trajectory_exact_format[0].keys())}")

def main():
    parser = argparse.ArgumentParser(description="Full Trajectory Teleoperation Recorder")
    parser.add_argument("--environment", type=str, default="Lift", 
                       help="Robosuite environment")
    parser.add_argument("--robot", type=str, default="Panda",
                       help="Robot to use")
    
    args = parser.parse_args()
    
    print("=== Full Trajectory Recorder ===")
    print("Records EVERY timestep (20Hz) during teleoperation")
    print("Captures joint positions + top/wrist camera images")
    print("Press Ctrl+Q to reset and save complete trajectory")
    print("=" * 50)
    
    # Create recorder
    recorder = FullTrajectoryRecorder(
        env_name=args.environment,
        robot=args.robot
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