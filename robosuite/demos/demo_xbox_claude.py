# """Teleoperate robot with Xbox Controller (game-like controls).

# Xbox Controller Layout:
#     Left Stick: Move end-effector in X-Y plane (forward/back, left/right)
#     Right Stick: Rotate end-effector (yaw left/right, pitch up/down)
#     Left/Right Triggers: Move end-effector up/down (Z axis)
#     Left/Right Bumpers: Roll rotation
#     A Button: Close gripper
#     B Button: Open gripper
#     X Button: Toggle camera view
#     Y Button: Reset environment
#     Start Button: Exit application
#     D-Pad: Fine position adjustments

# Requirements:
#     pip install pygame robosuite

# Note:
#     - Connect Xbox controller before running
#     - Controller provides smooth, game-like 6-DoF control
#     - Adjust --deadzone if experiencing stick drift (default: 0.15)
# """

# import argparse
# import time
# import numpy as np
# import pygame

# import robosuite as suite
# from robosuite import load_composite_controller_config
# from robosuite.controllers.composite.composite_controller import WholeBody
# from robosuite.wrappers import VisualizationWrapper
# from robosuite.utils.input_utils import *


# class XboxController:
#     """Xbox controller device for robot teleoperation."""
    
#     # Button mappings
#     BTN_A = 0
#     BTN_B = 1
#     BTN_X = 2
#     BTN_Y = 3
#     BTN_LB = 4
#     BTN_RB = 5
#     BTN_BACK = 6
#     BTN_START = 7
#     BTN_LSTICK = 8
#     BTN_RSTICK = 9
    
#     # Axis mappings
#     AXIS_LX = 0  # Left stick X
#     AXIS_LY = 1  # Left stick Y
#     AXIS_RX = 2  # Right stick X
#     AXIS_RY = 3  # Right stick Y
#     AXIS_LT = 4  # Left trigger
#     AXIS_RT = 5  # Right trigger
    
#     def __init__(self, env, pos_sensitivity=1.0, rot_sensitivity=1.0, deadzone=0.15):
#         """
#         Args:
#             env: Robosuite environment
#             pos_sensitivity: Position control sensitivity multiplier
#             rot_sensitivity: Rotation control sensitivity multiplier
#             deadzone: Deadzone threshold to prevent drift (0.0-1.0)
#         """
#         pygame.init()
#         pygame.joystick.init()
        
#         if pygame.joystick.get_count() == 0:
#             raise RuntimeError("No controller detected! Please connect an Xbox controller.")
        
#         self.controller = pygame.joystick.Joystick(0)
#         self.controller.init()
        
#         print(f"\n{'='*60}")
#         print(f"Controller connected: {self.controller.get_name()}")
#         print(f"Axes: {self.controller.get_numaxes()} | Buttons: {self.controller.get_numbuttons()}")
#         print(f"Deadzone: {deadzone:.2f}")
#         print(f"{'='*60}\n")
        
#         self.env = env
#         self.pos_sensitivity = pos_sensitivity * 0.05
#         self.rot_sensitivity = rot_sensitivity * 0.1
#         self.deadzone = deadzone
        
#         # Control state
#         self.active_robot = 0
#         self.gripper_state = {}
#         self.last_button_state = {}
        
#         # Initialize gripper state for all robots
#         for robot in env.robots:
#             for arm in robot.arms:
#                 if robot.gripper[arm] and robot.gripper[arm].dof > 0:
#                     self.gripper_state[f"{arm}_gripper"] = 0
    
#     def _apply_deadzone(self, value):
#         """Apply deadzone to axis values to prevent drift."""
#         if abs(value) < self.deadzone:
#             return 0.0
#         # Scale the remaining range
#         sign = 1 if value > 0 else -1
#         return sign * (abs(value) - self.deadzone) / (1.0 - self.deadzone)
    
#     def _get_trigger_value(self, axis):
#         """Get trigger value (normalize from -1~1 to 0~1)."""
#         raw = self.controller.get_axis(axis)
#         return (raw + 1.0) / 2.0
    
#     def start_control(self):
#         """Start control loop."""
#         pass
    
#     def get_controller_state(self):
#         """Process pygame events and return controller state."""
#         pygame.event.pump()
        
#         state = {
#             'axes': {},
#             'buttons': {},
#             'hat': (0, 0)
#         }
        
#         # Get all axis values with deadzone applied
#         for i in range(self.controller.get_numaxes()):
#             state['axes'][i] = self.controller.get_axis(i)
        
#         # Get all button states
#         for i in range(self.controller.get_numbuttons()):
#             state['buttons'][i] = self.controller.get_button(i)
        
#         # Get D-pad state
#         if self.controller.get_numhats() > 0:
#             state['hat'] = self.controller.get_hat(0)
        
#         return state
    
#     def input2action(self):
#         """Convert controller input to robot action."""
#         state = self.get_controller_state()
        
#         # Check for reset (Y button)
#         if state['buttons'][self.BTN_Y]:
#             if not self.last_button_state.get(self.BTN_Y, False):
#                 print("Resetting environment...")
#                 return None
#         self.last_button_state[self.BTN_Y] = state['buttons'][self.BTN_Y]
        
#         # Check for exit (Start button)
#         if state['buttons'][self.BTN_START]:
#             print("\nExiting...")
#             pygame.quit()
#             exit(0)
        
#         # Check for camera toggle (X button) - use button press event
#         if state['buttons'][self.BTN_X]:
#             if not self.last_button_state.get(self.BTN_X, False):
#                 # Get available cameras
#                 camera_names = self.env.sim.model.camera_names
#                 current_cam_id = self.env.viewer.camera_id
#                 next_cam_id = (current_cam_id + 1) % len(camera_names)
                
#                 # Set new camera
#                 self.env.viewer.set_camera(camera_id=next_cam_id)
#                 print(f"Camera: {camera_names[next_cam_id]} (#{next_cam_id})")
#         self.last_button_state[self.BTN_X] = state['buttons'][self.BTN_X]
        
#         # Get active robot
#         active_robot = self.env.robots[self.active_robot]
        
#         # Build action dictionary
#         action_dict = {}
        
#         # Process for each arm
#         for arm in active_robot.arms:
#             # --- Position Control (Left Stick + Triggers) ---
#             left_x = self._apply_deadzone(state['axes'][self.AXIS_LX])
#             left_y = self._apply_deadzone(state['axes'][self.AXIS_LY])
            
#             # Triggers: Z axis
#             lt_value = self._get_trigger_value(self.AXIS_LT)
#             rt_value = self._get_trigger_value(self.AXIS_RT)
#             z_movement = (rt_value - lt_value)
            
#             # D-pad for fine adjustments
#             dpad_x, dpad_y = state['hat']
            
#             # Combine position inputs
#             pos_x = left_x + dpad_x * 0.3
#             pos_y = -left_y - dpad_y * 0.3  # Invert Y
#             pos_z = z_movement
            
#             position = np.array([pos_x, pos_y, pos_z]) * self.pos_sensitivity
            
#             # --- Rotation Control (Right Stick + Bumpers) ---
#             right_x = self._apply_deadzone(state['axes'][self.AXIS_RX])
#             right_y = self._apply_deadzone(state['axes'][self.AXIS_RY])
            
#             # Bumpers: Roll
#             roll = 0.0
#             if state['buttons'][self.BTN_RB]:
#                 roll = 1.0
#             elif state['buttons'][self.BTN_LB]:
#                 roll = -1.0
            
#             # Rotation: [roll, pitch, yaw]
#             rotation = np.array([roll, -right_y, right_x]) * self.rot_sensitivity
            
#             # Combine into delta command
#             action_dict[f"{arm}_delta"] = np.concatenate([position, rotation])
#             action_dict[f"{arm}_abs"] = np.concatenate([position, rotation])
            
#             # --- Gripper Control (A/B buttons) ---
#             if active_robot.gripper[arm] and active_robot.gripper[arm].dof > 0:
#                 gripper_action = 0.0
                
#                 # A button: close gripper
#                 if state['buttons'][self.BTN_A]:
#                     gripper_action = 1.0
#                 # B button: open gripper
#                 elif state['buttons'][self.BTN_B]:
#                     gripper_action = -1.0
                
#                 action_dict[f"{arm}_gripper"] = np.array([gripper_action] * active_robot.gripper[arm].dof)
#                 self.gripper_state[f"{arm}_gripper"] = gripper_action
        
#         return action_dict


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Xbox Controller Robot Teleoperation")
#     parser.add_argument(
#         "--environment",
#         type=str,
#         default=None,
#         help="Environment name (leave empty for interactive selection)"
#     )
#     parser.add_argument(
#         "--robots",
#         nargs="+",
#         type=str,
#         default=None,
#         help="Robot(s) to use (leave empty for interactive selection)"
#     )
#     parser.add_argument(
#         "--config",
#         type=str,
#         default="default",
#         help="Environment configuration (for TwoArm environments)"
#     )
#     parser.add_argument(
#         "--controller",
#         type=str,
#         default=None,
#         help="Controller type or None for robot default"
#     )
#     parser.add_argument(
#         "--pos-sensitivity",
#         type=float,
#         default=1.0,
#         help="Position control sensitivity (0.1-5.0)"
#     )
#     parser.add_argument(
#         "--rot-sensitivity",
#         type=float,
#         default=1.0,
#         help="Rotation control sensitivity (0.1-5.0)"
#     )
#     parser.add_argument(
#         "--deadzone",
#         type=float,
#         default=0.15,
#         help="Controller deadzone to prevent drift (0.0-0.5, default: 0.15)"
#     )
#     parser.add_argument(
#         "--max-fr",
#         type=int,
#         default=20,
#         help="Maximum frame rate (20 = real-time)"
#     )
#     parser.add_argument(
#         "--camera",
#         type=str,
#         default="agentview",
#         help="Initial camera view"
#     )
#     args = parser.parse_args()
    
#     # Print welcome message
#     print("\n" + "="*60)
#     print("Xbox Controller Robot Teleoperation")
#     print("="*60)
#     print(f"Robosuite version: {suite.__version__}")
#     print(suite.__logo__)
    
#     # Create environment options
#     options = {}
    
#     # Interactive environment selection
#     if args.environment is None:
#         options["env_name"] = choose_environment()
#     else:
#         options["env_name"] = args.environment
    
#     # Handle multi-arm environments
#     if "TwoArm" in options["env_name"]:
#         options["env_configuration"] = choose_multi_arm_config()
        
#         if options["env_configuration"] == "single-robot":
#             options["robots"] = choose_robots(
#                 exclude_bimanual=False, 
#                 use_humanoids=True, 
#                 exclude_single_arm=True
#             )
#         else:
#             options["robots"] = []
#             for i in range(2):
#                 print(f"Please choose Robot {i}...\n")
#                 options["robots"].append(
#                     choose_robots(exclude_bimanual=False, use_humanoids=True)
#                 )
#     # Handle humanoid environments
#     elif "Humanoid" in options["env_name"]:
#         if args.robots is None:
#             options["robots"] = choose_robots(use_humanoids=True)
#         else:
#             options["robots"] = args.robots
#     # Standard single-arm environments
#     else:
#         if args.robots is None:
#             options["robots"] = choose_robots(
#                 exclude_bimanual=False, 
#                 use_humanoids=True
#             )
#         else:
#             options["robots"] = args.robots
    
#     # Ensure robots is a list
#     if not isinstance(options["robots"], list):
#         options["robots"] = [options["robots"]]
    
#     print(f"\n{'='*60}")
#     print(f"Environment: {options['env_name']}")
#     print(f"Robot(s): {options['robots']}")
#     print(f"{'='*60}")
    
#     # Load controller config
#     try:
#         controller_config = load_composite_controller_config(
#             controller=args.controller,
#             robot=options["robots"][0],
#         )
#         print(f"Controller: {args.controller if args.controller else 'default'}")
#     except Exception as e:
#         print(f"Error loading controller: {e}")
#         print("Using default controller...")
#         controller_config = load_composite_controller_config(
#             controller=None,
#             robot=options["robots"][0],
#         )
    
#     options["controller_configs"] = controller_config
    
#     # Create environment
#     print("\nInitializing environment...")
#     env = suite.make(
#         **options,
#         has_renderer=True,
#         has_offscreen_renderer=False,
#         render_camera=args.camera,
#         ignore_done=True,
#         use_camera_obs=False,
#         control_freq=20,
#         renderer="mjviewer",
#     )
    
#     # Wrap with visualization
#     env = VisualizationWrapper(env, indicator_configs=None)
    
#     # Print available cameras
#     print(f"\nAvailable cameras: {list(env.sim.model.camera_names)}")
    
#     # Initialize Xbox controller
#     try:
#         device = XboxController(
#             env=env,
#             pos_sensitivity=args.pos_sensitivity,
#             rot_sensitivity=args.rot_sensitivity,
#             deadzone=args.deadzone,
#         )
#     except RuntimeError as e:
#         print(f"\nError: {e}")
#         print("Please connect an Xbox controller and try again.")
#         exit(1)
    
#     # Setup printing
#     np.set_printoptions(formatter={"float": lambda x: "{0:0.3f}".format(x)})
    
#     # Print controls
#     print("\nControls:")
#     print("  Left Stick:          Move X-Y (forward/back, left/right)")
#     print("  Right Stick:         Rotate (yaw, pitch)")
#     print("  Left/Right Triggers: Move Z (down/up)")
#     print("  Left/Right Bumpers:  Roll rotation")
#     print("  D-Pad:              Fine adjustments")
#     print("  A Button:           Close gripper")
#     print("  B Button:           Open gripper")
#     print("  X Button:           Cycle camera")
#     print("  Y Button:           Reset environment")
#     print("  Start Button:       Exit")
#     print("="*60)
    
#     # Main control loop
#     try:
#         while True:
#             # Reset environment
#             obs = env.reset()
#             env.render()
            
#             # Initialize device control
#             device.start_control()
            
#             # Track previous gripper actions
#             all_prev_gripper_actions = [
#                 {
#                     f"{robot_arm}_gripper": np.repeat([0], robot.gripper[robot_arm].dof)
#                     for robot_arm in robot.arms
#                     if robot.gripper[robot_arm] and robot.gripper[robot_arm].dof > 0
#                 }
#                 for robot in env.robots
#             ]
            
#             print("\nReady! Use Xbox controller to control robot.")
#             print("(If robot drifts, increase --deadzone value)")
            
#             # Episode loop
#             while True:
#                 start = time.time()
                
#                 # Get active robot
#                 active_robot = env.robots[device.active_robot]
                
#                 # Get action from controller
#                 input_ac_dict = device.input2action()
                
#                 # Check for reset
#                 if input_ac_dict is None:
#                     break
                
#                 # Build action dictionary
#                 action_dict = {}
                
#                 # Set arm actions based on controller type
#                 for arm in active_robot.arms:
#                     if isinstance(active_robot.composite_controller, WholeBody):
#                         controller_input_type = active_robot.composite_controller.joint_action_policy.input_type
#                     else:
#                         controller_input_type = active_robot.part_controllers[arm].input_type
                    
#                     if controller_input_type == "delta":
#                         action_dict[arm] = input_ac_dict[f"{arm}_delta"]
#                     elif controller_input_type == "absolute":
#                         action_dict[arm] = input_ac_dict[f"{arm}_abs"]
#                     else:
#                         raise ValueError(f"Unknown controller input type: {controller_input_type}")
                    
#                     # Add gripper action
#                     if f"{arm}_gripper" in input_ac_dict:
#                         action_dict[f"{arm}_gripper"] = input_ac_dict[f"{arm}_gripper"]
                
#                 # Create environment action
#                 env_action = [
#                     robot.create_action_vector(all_prev_gripper_actions[i])
#                     for i, robot in enumerate(env.robots)
#                 ]
#                 env_action[device.active_robot] = active_robot.create_action_vector(action_dict)
#                 env_action = np.concatenate(env_action)
                
#                 # Update previous gripper actions
#                 for gripper_ac in all_prev_gripper_actions[device.active_robot]:
#                     if gripper_ac in action_dict:
#                         all_prev_gripper_actions[device.active_robot][gripper_ac] = action_dict[gripper_ac]
                
#                 # Step environment
#                 env.step(env_action)
#                 env.render()
                
#                 # Frame rate limiting
#                 if args.max_fr is not None:
#                     elapsed = time.time() - start
#                     diff = 1 / args.max_fr - elapsed
#                     if diff > 0:
#                         time.sleep(diff)
    
#     except KeyboardInterrupt:
#         print("\n\nInterrupted by user.")
#     except Exception as e:
#         print(f"\nError: {e}")
#         import traceback
#         traceback.print_exc()
#     finally:
#         pygame.quit()
#         print("\nGoodbye!")
"""Teleoperate robot with Xbox Controller (game-like controls).

Xbox Controller Layout:
    Left Stick: Move end-effector in X-Y plane (forward/back, left/right)
    Right Stick: Rotate end-effector (yaw left/right, pitch up/down)
    Left/Right Triggers: Move end-effector up/down (Z axis)
    Left/Right Bumpers: Roll rotation
    A Button: Close gripper
    B Button: Open gripper
    X Button: Toggle camera view
    Y Button: Reset environment
    Start Button: Exit application
    D-Pad: Fine position adjustments

Requirements:
    pip install pygame robosuite

Note:
    - Connect Xbox controller before running
    - Controller provides smooth, game-like 6-DoF control
    - Adjust --deadzone if experiencing stick drift (default: 0.15)
"""

import argparse
import time
import numpy as np
import pygame

import robosuite as suite
from robosuite import load_composite_controller_config
from robosuite.controllers.composite.composite_controller import WholeBody
from robosuite.wrappers import VisualizationWrapper
from robosuite.utils.input_utils import *


class XboxController:
    """Xbox controller device for robot teleoperation."""
    
    # Button mappings
    BTN_A = 0
    BTN_B = 1
    BTN_X = 2
    BTN_Y = 3
    BTN_LB = 4
    BTN_RB = 5
    BTN_BACK = 6
    BTN_START = 7
    BTN_LSTICK = 8
    BTN_RSTICK = 9
    
    # Axis mappings
    AXIS_LX = 0  # Left stick X
    AXIS_LY = 1  # Left stick Y
    AXIS_RX = 2  # Right stick X
    AXIS_RY = 3  # Right stick Y
    AXIS_LT = 4  # Left trigger
    AXIS_RT = 5  # Right trigger
    
    def __init__(self, env, pos_sensitivity=1.0, rot_sensitivity=1.0, deadzone=0.9):
        """
        Args:
            env: Robosuite environment
            pos_sensitivity: Position control sensitivity multiplier
            rot_sensitivity: Rotation control sensitivity multiplier
            deadzone: Deadzone threshold to prevent drift (0.0-1.0)
        """
        pygame.init()
        pygame.joystick.init()
        
        if pygame.joystick.get_count() == 0:
            raise RuntimeError("No controller detected! Please connect an Xbox controller.")
        
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()
        
        print(f"\n{'='*60}")
        print(f"Controller connected: {self.controller.get_name()}")
        print(f"Axes: {self.controller.get_numaxes()} | Buttons: {self.controller.get_numbuttons()}")
        print(f"Deadzone: {deadzone:.2f}")
        print(f"{'='*60}\n")
        
        self.env = env
        self.pos_sensitivity = pos_sensitivity * 0.15  # Increased from 0.05
        self.rot_sensitivity = rot_sensitivity * 0.3   # Increased from 0.1
        self.deadzone = deadzone
        self.camera_id = 0  # Track camera index
        
        # Control state
        self.active_robot = 0
        self.gripper_state = {}
        self.last_button_state = {}
        
        # Initialize gripper state for all robots
        for robot in env.robots:
            for arm in robot.arms:
                if robot.gripper[arm] and robot.gripper[arm].dof > 0:
                    self.gripper_state[f"{arm}_gripper"] = 0
    
    def _apply_deadzone(self, value):
        """Apply deadzone to axis values to prevent drift."""
        if abs(value) < self.deadzone:
            return 0.0
        # Scale the remaining range
        sign = 1 if value > 0 else -1
        return sign * (abs(value) - self.deadzone) / (1.0 - self.deadzone)
    
    def _get_trigger_value(self, axis):
        """Get trigger value (normalize from -1~1 to 0~1)."""
        raw = self.controller.get_axis(axis)
        return (raw + 1.0) / 2.0
    
    def start_control(self):
        """Start control loop."""
        pass
    
    def get_controller_state(self):
        """Process pygame events and return controller state."""
        pygame.event.pump()
        
        state = {
            'axes': {},
            'buttons': {},
            'hat': (0, 0)
        }
        
        # Get all axis values with deadzone applied
        for i in range(self.controller.get_numaxes()):
            state['axes'][i] = self.controller.get_axis(i)
        
        # Get all button states
        for i in range(self.controller.get_numbuttons()):
            state['buttons'][i] = self.controller.get_button(i)
        
        # Get D-pad state
        if self.controller.get_numhats() > 0:
            state['hat'] = self.controller.get_hat(0)
        
        return state
    
    def input2action(self):
        """Convert controller input to robot action."""
        state = self.get_controller_state()
        
        # Check for reset (Y button)
        if state['buttons'][self.BTN_Y]:
            if not self.last_button_state.get(self.BTN_Y, False):
                print("Resetting environment...")
                return None
        self.last_button_state[self.BTN_Y] = state['buttons'][self.BTN_Y]
        
        # Check for exit (Start button)
        if state['buttons'][self.BTN_START]:
            print("\nExiting...")
            pygame.quit()
            exit(0)
        
        # Check for camera toggle (X button) - use button press event
        if state['buttons'][self.BTN_X]:
            if not self.last_button_state.get(self.BTN_X, False):
                # Get available cameras
                camera_names = self.env.sim.model.camera_names
                current_cam_id = self.env.viewer.camera_id
                next_cam_id = (current_cam_id + 1) % len(camera_names)
                
                # Set new camera
                self.env.viewer.set_camera(camera_id=next_cam_id)
                print(f"Camera: {camera_names[next_cam_id]} (#{next_cam_id})")
        self.last_button_state[self.BTN_X] = state['buttons'][self.BTN_X]
        
        # Get active robot
        active_robot = self.env.robots[self.active_robot]
        
        # Build action dictionary
        action_dict = {}
        
        # Process for each arm
        for arm in active_robot.arms:
            # --- Position Control (Left Stick + Triggers) ---
            left_x = self._apply_deadzone(state['axes'][self.AXIS_LX])
            left_y = self._apply_deadzone(state['axes'][self.AXIS_LY])
            
            # Triggers: Z axis
            lt_value = self._get_trigger_value(self.AXIS_LT)
            rt_value = self._get_trigger_value(self.AXIS_RT)
            z_movement = (rt_value - lt_value)
            
            # D-pad for fine adjustments
            dpad_x, dpad_y = state['hat']
            
            # Combine position inputs
            pos_x = left_x + dpad_x * 0.3
            pos_y = -left_y - dpad_y * 0.3  # Invert Y
            pos_z = z_movement
            
            position = np.array([pos_x, pos_y, pos_z]) * self.pos_sensitivity
            
            # --- Rotation Control (Right Stick + Bumpers) ---
            right_x = self._apply_deadzone(state['axes'][self.AXIS_RX])
            right_y = self._apply_deadzone(state['axes'][self.AXIS_RY])
            
            # Bumpers: Roll
            roll = 0.0
            if state['buttons'][self.BTN_RB]:
                roll = 1.0
            elif state['buttons'][self.BTN_LB]:
                roll = -1.0
            
            # Rotation: [roll, pitch, yaw]
            rotation = np.array([roll, -right_y, right_x]) * self.rot_sensitivity
            
            # Combine into delta command
            action_dict[f"{arm}_delta"] = np.concatenate([position, rotation])
            action_dict[f"{arm}_abs"] = np.concatenate([position, rotation])
            
            # --- Gripper Control (A/B buttons) ---
            if active_robot.gripper[arm] and active_robot.gripper[arm].dof > 0:
                gripper_action = 0.0
                
                # A button: close gripper
                if state['buttons'][self.BTN_A]:
                    gripper_action = 1.0
                # B button: open gripper
                elif state['buttons'][self.BTN_B]:
                    gripper_action = -1.0
                
                action_dict[f"{arm}_gripper"] = np.array([gripper_action] * active_robot.gripper[arm].dof)
                self.gripper_state[f"{arm}_gripper"] = gripper_action
        
        return action_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Xbox Controller Robot Teleoperation")
    parser.add_argument(
        "--environment",
        type=str,
        default=None,
        help="Environment name (leave empty for interactive selection)"
    )
    parser.add_argument(
        "--robots",
        nargs="+",
        type=str,
        default=None,
        help="Robot(s) to use (leave empty for interactive selection)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="default",
        help="Environment configuration (for TwoArm environments)"
    )
    parser.add_argument(
        "--controller",
        type=str,
        default=None,
        help="Controller type or None for robot default"
    )
    parser.add_argument(
        "--pos-sensitivity",
        type=float,
        default=1.0,
        help="Position control sensitivity (0.1-5.0)"
    )
    parser.add_argument(
        "--rot-sensitivity",
        type=float,
        default=1.0,
        help="Rotation control sensitivity (0.1-5.0)"
    )
    parser.add_argument(
        "--deadzone",
        type=float,
        default=0.15,
        help="Controller deadzone to prevent drift (0.0-0.5, default: 0.15)"
    )
    parser.add_argument(
        "--max-fr",
        type=int,
        default=20,
        help="Maximum frame rate (20 = real-time)"
    )
    parser.add_argument(
        "--camera",
        type=str,
        default="agentview",
        help="Initial camera view"
    )
    args = parser.parse_args()
    
    # Print welcome message
    print("\n" + "="*60)
    print("Xbox Controller Robot Teleoperation")
    print("="*60)
    print(f"Robosuite version: {suite.__version__}")
    print(suite.__logo__)
    
    # Create environment options
    options = {}
    
    # Interactive environment selection
    if args.environment is None:
        options["env_name"] = choose_environment()
    else:
        options["env_name"] = args.environment
    
    # Handle multi-arm environments
    if "TwoArm" in options["env_name"]:
        options["env_configuration"] = choose_multi_arm_config()
        
        if options["env_configuration"] == "single-robot":
            options["robots"] = choose_robots(
                exclude_bimanual=False, 
                use_humanoids=True, 
                exclude_single_arm=True
            )
        else:
            options["robots"] = []
            for i in range(2):
                print(f"Please choose Robot {i}...\n")
                options["robots"].append(
                    choose_robots(exclude_bimanual=False, use_humanoids=True)
                )
    # Handle humanoid environments
    elif "Humanoid" in options["env_name"]:
        if args.robots is None:
            options["robots"] = choose_robots(use_humanoids=True)
        else:
            options["robots"] = args.robots
    # Standard single-arm environments
    else:
        if args.robots is None:
            options["robots"] = choose_robots(
                exclude_bimanual=False, 
                use_humanoids=True
            )
        else:
            options["robots"] = args.robots
    
    # Ensure robots is a list
    if not isinstance(options["robots"], list):
        options["robots"] = [options["robots"]]
    
    print(f"\n{'='*60}")
    print(f"Environment: {options['env_name']}")
    print(f"Robot(s): {options['robots']}")
    print(f"{'='*60}")
    
    # Load controller config
    try:
        controller_config = load_composite_controller_config(
            controller=args.controller,
            robot=options["robots"][0],
        )
        print(f"Controller: {args.controller if args.controller else 'default'}")
    except Exception as e:
        print(f"Error loading controller: {e}")
        print("Using default controller...")
        controller_config = load_composite_controller_config(
            controller=None,
            robot=options["robots"][0],
        )
    
    options["controller_configs"] = controller_config
    
    # Create environment
    print("\nInitializing environment...")
    env = suite.make(
        **options,
        has_renderer=True,
        has_offscreen_renderer=False,
        render_camera=args.camera,
        ignore_done=True,
        use_camera_obs=False,
        control_freq=20,
        renderer="mjviewer",
    )
    
    # Wrap with visualization
    env = VisualizationWrapper(env, indicator_configs=None)
    
    # Print available cameras
    print(f"\nAvailable cameras: {list(env.sim.model.camera_names)}")
    
    # Initialize Xbox controller
    try:
        device = XboxController(
            env=env,
            pos_sensitivity=args.pos_sensitivity,
            rot_sensitivity=args.rot_sensitivity,
            deadzone=args.deadzone,
        )
    except RuntimeError as e:
        print(f"\nError: {e}")
        print("Please connect an Xbox controller and try again.")
        exit(1)
    
    # Setup printing
    np.set_printoptions(formatter={"float": lambda x: "{0:0.3f}".format(x)})
    
    # Print controls
    print("\nControls:")
    print("  Left Stick:          Move X-Y (forward/back, left/right)")
    print("  Right Stick:         Rotate (yaw, pitch)")
    print("  Left/Right Triggers: Move Z (down/up)")
    print("  Left/Right Bumpers:  Roll rotation")
    print("  D-Pad:              Fine adjustments")
    print("  A Button:           Close gripper")
    print("  B Button:           Open gripper")
    print("  X Button:           Cycle camera")
    print("  Y Button:           Reset environment")
    print("  Start Button:       Exit")
    print("="*60)
    
    # Main control loop
    try:
        while True:
            # Reset environment
            obs = env.reset()
            env.render()
            
            # Initialize device control
            device.start_control()
            
            # Track previous gripper actions
            all_prev_gripper_actions = [
                {
                    f"{robot_arm}_gripper": np.repeat([0], robot.gripper[robot_arm].dof)
                    for robot_arm in robot.arms
                    if robot.gripper[robot_arm] and robot.gripper[robot_arm].dof > 0
                }
                for robot in env.robots
            ]
            
            print("\nReady! Use Xbox controller to control robot.")
            print("(If robot drifts, increase --deadzone value)")
            
            # Episode loop
            while True:
                start = time.time()
                
                # Get active robot
                active_robot = env.robots[device.active_robot]
                
                # Get action from controller
                input_ac_dict = device.input2action()
                
                # Check for reset
                if input_ac_dict is None:
                    break
                
                # Build action dictionary
                action_dict = {}
                
                # Set arm actions based on controller type
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
                        raise ValueError(f"Unknown controller input type: {controller_input_type}")
                    
                    # Add gripper action
                    if f"{arm}_gripper" in input_ac_dict:
                        action_dict[f"{arm}_gripper"] = input_ac_dict[f"{arm}_gripper"]
                
                # Create environment action
                env_action = [
                    robot.create_action_vector(all_prev_gripper_actions[i])
                    for i, robot in enumerate(env.robots)
                ]
                env_action[device.active_robot] = active_robot.create_action_vector(action_dict)
                env_action = np.concatenate(env_action)
                
                # Update previous gripper actions
                for gripper_ac in all_prev_gripper_actions[device.active_robot]:
                    if gripper_ac in action_dict:
                        all_prev_gripper_actions[device.active_robot][gripper_ac] = action_dict[gripper_ac]
                
                # Step environment
                env.step(env_action)
                env.render()
                
                # Frame rate limiting
                if args.max_fr is not None:
                    elapsed = time.time() - start
                    diff = 1 / args.max_fr - elapsed
                    if diff > 0:
                        time.sleep(diff)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        print("\nGoodbye!")