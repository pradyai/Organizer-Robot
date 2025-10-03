"""Teleoperate robot with Xbox Controller (game-like controls).

Xbox Controller Layout:
    Left Analog Stick: Move end-effector forward/back, left/right (X-Y axes)
    Right Analog Stick: Move end-effector up/down (Z axis), yaw rotation
    Left/Right Bumpers: Roll rotation
    A Button: Close gripper
    B Button: Open gripper
    X Button: Toggle camera view
    Y Button: Reset environment
    Start Button: Exit application

Requirements:
    pip install pygame robosuite

Note:
    - Connect Xbox controller before running
    - If the robot drifts, increase the --deadzone value (e.g., --deadzone 0.3)
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
    AXIS_LX = 0
    AXIS_LY = 1
    AXIS_RX = 2
    AXIS_RY = 3
    # NOTE: Triggers (AXIS_LT=4, AXIS_RT=5) are not used for movement in this version.

    def __init__(self, env, pos_sensitivity=1.0, rot_sensitivity=1.0, deadzone=0.1):
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            raise RuntimeError("No controller detected! Please connect an Xbox controller.")

        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()

        print(f"\n{'='*60}")
        print(f"Controller connected: {self.controller.get_name()}")
        print(f"Deadzone set to: {deadzone:.2f}")
        print(f"{'='*60}\n")

        self.env = env
        self.pos_sensitivity = pos_sensitivity * 0.08
        self.rot_sensitivity = rot_sensitivity * 0.15
        self.deadzone = deadzone
        self.camera_id = 0

        # Control state
        self.active_robot = 0
        self.last_button_state = {i: 0 for i in range(self.controller.get_numbuttons())}

    def _deadzone_axis(self, value):
        """Apply a deadzone to an analog stick axis value."""
        return value if abs(value) > self.deadzone else 0.0

    def start_control(self):
        """Start control loop (placeholder)."""
        pass

    def get_controller_state(self):
        """Process pygame events and return the current controller state."""
        pygame.event.pump()
        state = {
            'axes': {i: self.controller.get_axis(i) for i in range(self.controller.get_numaxes())},
            'buttons': {i: self.controller.get_button(i) for i in range(self.controller.get_numbuttons())},
        }
        return state

    def input2action(self):
        """Convert controller input to a robot action dictionary."""
        state = self.get_controller_state()
        
        # Handle non-movement buttons (Reset, Exit, Camera)
        if state['buttons'][self.BTN_Y] and not self.last_button_state[self.BTN_Y]:
            print("Resetting environment...")
            self.last_button_state = state['buttons']
            return None
        
        if state['buttons'][self.BTN_START]:
            print("\nExiting...")
            pygame.quit()
            exit(0)

        if state['buttons'][self.BTN_X] and not self.last_button_state[self.BTN_X]:
            camera_names = self.env.sim.model.camera_names
            self.camera_id = (self.camera_id + 1) % len(camera_names)
            self.env.viewer.set_camera(camera_id=self.camera_id)
            print(f"Switched to Camera: {camera_names[self.camera_id]} (#{self.camera_id})")
        
        self.last_button_state = state['buttons']

        active_robot = self.env.robots[self.active_robot]
        action_dict = {}

        # Handle Robot Movement
        for arm in active_robot.arms:
            # --- MODIFIED: Position Control using Analog Sticks ---
            # Left stick for X-Y movement
            x_movement = self._deadzone_axis(state['axes'][self.AXIS_LX])
            y_movement = -self._deadzone_axis(state['axes'][self.AXIS_LY]) # Pygame's Y-axis is inverted
            
            # Right stick for Z movement
            z_movement = -self._deadzone_axis(state['axes'][self.AXIS_RY]) # Pygame's Y-axis is inverted

            position = np.array([x_movement, y_movement, z_movement]) * self.pos_sensitivity

            # --- MODIFIED: Rotation Control using Right Stick + Bumpers ---
            # Bumpers for Roll
            roll = 0.0
            if state['buttons'][self.BTN_RB]: roll = 1.0
            elif state['buttons'][self.BTN_LB]: roll = -1.0
            
            # Right stick for Yaw
            yaw = self._deadzone_axis(state['axes'][self.AXIS_RX])
            
            pitch = 0.0 # Pitch is not controlled in this scheme

            rotation = np.array([roll, pitch, yaw]) * self.rot_sensitivity

            # Store action components
            action_dict[f"{arm}_delta"] = np.concatenate([position, rotation])
            action_dict[f"{arm}_abs"] = np.concatenate([position, rotation])

            # Gripper Control
            if active_robot.gripper[arm] and active_robot.gripper[arm].dof > 0:
                gripper_action = 0.0
                if state['buttons'][self.BTN_A]: gripper_action = 1.0
                elif state['buttons'][self.BTN_B]: gripper_action = -1.0
                action_dict[f"{arm}_gripper"] = np.array([gripper_action] * active_robot.gripper[arm].dof)
        
        return action_dict

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Xbox Controller Robot Teleoperation")
    parser.add_argument("--environment", type=str, default=None, help="Environment name")
    parser.add_argument("--robots", nargs="+", type=str, default=None, help="Robot(s) to use")
    parser.add_argument("--config", type=str, default="default", help="Environment configuration")
    parser.add_argument("--controller", type=str, default=None, help="Controller type")
    parser.add_argument("--pos-sensitivity", type=float, default=1.0, help="Position control sensitivity")
    parser.add_argument("--rot-sensitivity", type=float, default=1.0, help="Rotation control sensitivity")
    parser.add_argument("--deadzone", type=float, default=0.1, help="Controller deadzone for analog sticks to prevent drift")
    parser.add_argument("--max-fr", type=int, default=20, help="Maximum frame rate")
    parser.add_argument("--camera", type=str, default="agentview", help="Initial camera view")
    args = parser.parse_args()
    
    # --- Environment Setup ---
    print("\n" + "="*60)
    print("Xbox Controller Robot Teleoperation")
    print("="*60)
    print(f"Robosuite version: {suite.__version__}")
    print(suite.__logo__)
    
    options = {}
    options["env_name"] = args.environment if args.environment else choose_environment()
    
    if "TwoArm" in options["env_name"]:
        options["env_configuration"] = choose_multi_arm_config()
        if options["env_configuration"] == "single-robot":
            options["robots"] = choose_robots(exclude_bimanual=False, use_humanoids=True, exclude_single_arm=True)
        else:
            options["robots"] = [choose_robots(exclude_bimanual=False, use_humanoids=True) for _ in range(2)]
    else:
        options["robots"] = args.robots if args.robots else choose_robots(exclude_bimanual=False, use_humanoids=True)
    
    if not isinstance(options["robots"], list):
        options["robots"] = [options["robots"]]
    
    print(f"\n{'='*60}")
    print(f"Environment: {options['env_name']}")
    print(f"Robot(s): {options['robots']}")
    print(f"{'='*60}")
    
    controller_config = load_composite_controller_config(controller=args.controller, robot=options["robots"][0])
    options["controller_configs"] = controller_config
    
    env = suite.make(**options, has_renderer=True, has_offscreen_renderer=False, render_camera=args.camera, ignore_done=True, use_camera_obs=False, control_freq=20, renderer="mjviewer")
    env = VisualizationWrapper(env, indicator_configs=None)
    
    try:
        device = XboxController(env=env, pos_sensitivity=args.pos_sensitivity, rot_sensitivity=args.rot_sensitivity, deadzone=args.deadzone)
    except RuntimeError as e:
        print(f"\nError: {e}\nPlease connect an Xbox controller and try again.")
        exit(1)
        
    np.set_printoptions(formatter={"float": lambda x: "{0:0.3f}".format(x)})
    
    # --- MODIFIED: Updated control instructions ---
    print("\nControls:")
    print("  Left Analog Stick:   Move X-Y (fwd/back, left/right)")
    print("  Right Analog Stick:  Move Z (up/down) and Yaw (turn)")
    print("  Left/Right Bumpers:  Roll rotation")
    print("  A Button:            Close gripper")
    print("  B Button:            Open gripper")
    print("  X Button:            Cycle camera")
    print("  Y Button:            Reset environment")
    print("  Start Button:        Exit")
    print("="*60)
    
    # --- Main Control Loop ---
    try:
        while True:
            obs = env.reset()
            env.render()
            device.start_control()
            
            all_prev_gripper_actions = [{f"{arm}_gripper": np.zeros(robot.gripper[arm].dof) for arm in robot.arms if robot.gripper[arm] and robot.gripper[arm].dof > 0} for robot in env.robots]
            
            print("\nReady! Use Xbox controller to control the robot.")
            print(f"(If robot drifts, restart with a higher --deadzone value, e.g., --deadzone 0.3)")
            
            while True:
                start_time = time.time()
                active_robot = env.robots[device.active_robot]
                input_ac_dict = device.input2action()
                
                if input_ac_dict is None: break

                action_dict = {}
                for arm in active_robot.arms:
                    controller = active_robot.composite_controller if isinstance(active_robot.composite_controller, WholeBody) else active_robot.part_controllers[arm]
                    input_type = controller.joint_action_policy.input_type if isinstance(controller, WholeBody) else controller.input_type
                    
                    action_key = f"{arm}_delta" if input_type == "delta" else f"{arm}_abs"
                    action_dict[arm] = input_ac_dict[action_key]
                    
                    if f"{arm}_gripper" in input_ac_dict:
                        action_dict[f"{arm}_gripper"] = input_ac_dict[f"{arm}_gripper"]

                env_action = [robot.create_action_vector(all_prev_gripper_actions[i]) for i, robot in enumerate(env.robots)]
                env_action[device.active_robot] = active_robot.create_action_vector(action_dict)
                env_action = np.concatenate(env_action)
                
                for gripper_ac in all_prev_gripper_actions[device.active_robot]:
                    if gripper_ac in action_dict:
                        all_prev_gripper_actions[device.active_robot][gripper_ac] = action_dict[gripper_ac]
                
                env.step(env_action)
                env.render()
                
                if args.max_fr is not None:
                    elapsed = time.time() - start_time
                    sleep_time = (1 / args.max_fr) - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    finally:
        pygame.quit()
        print("\nGoodbye!")