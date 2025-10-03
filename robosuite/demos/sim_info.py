# import argparse
# import time

# import numpy as np

# import robosuite as suite
# from robosuite import load_composite_controller_config
# from robosuite.controllers.composite.composite_controller import WholeBody
# from robosuite.wrappers import VisualizationWrapper
# from robosuite.utils.input_utils import *

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--environment", type=str, default="Lift")
#     parser.add_argument(
#         "--robots",
#         nargs="+",
#         type=str,
#         default="SO101Arm",
#         help="Which robot(s) to use in the env",
#     )
#     parser.add_argument(
#         "--config",
#         type=str,
#         default="default",
#         help="Specified environment configuration if necessary",
#     )
#     parser.add_argument(
#         "--arm",
#         type=str,
#         default="right",
#         help="Which arm to control (eg bimanual) 'right' or 'left'",
#     )
#     parser.add_argument(
#         "--switch-on-grasp",
#         action="store_true",
#         help="Switch gripper control on gripper action",
#     )
#     parser.add_argument(
#         "--toggle-camera-on-grasp",
#         action="store_true",
#         help="Switch camera angle on gripper action",
#     )
#     parser.add_argument(
#         "--controller",
#         type=str,
#         default=None,
#         help="Choice of controller. Can be generic (eg. 'BASIC' or 'WHOLE_BODY_MINK_IK') or json file (see robosuite/controllers/config for examples) or None to get the robot's default controller if it exists",
#     )
#     parser.add_argument("--device", type=str, default="keyboard")
#     parser.add_argument(
#         "--pos-sensitivity",
#         type=float,
#         default=1.0,
#         help="How much to scale position user inputs",
#     )
#     parser.add_argument(
#         "--rot-sensitivity",
#         type=float,
#         default=1.0,
#         help="How much to scale rotation user inputs",
#     )
#     parser.add_argument(
#         "--max_fr",
#         default=20,
#         type=int,
#         help="Sleep when simluation runs faster than specified frame rate; 20 fps is real time.",
#     )
#     parser.add_argument(
#         "--reverse_xy",
#         type=bool,
#         default=False,
#         help="(DualSense Only)Reverse the effect of the x and y axes of the joystick.It is used to handle the case that the left/right and front/back sides of the view are opposite to the LX and LY of the joystick(Push LX up but the robot move left in your view)",
#     )
#     args = parser.parse_args()


#     # # Create argument configuration
#     # config = {
#     #     "env_name": args.environment,
#     #     "robots": args.robots,
#     #     "controller_configs": controller_config,
#     # }

#     # # Check if we're using a multi-armed environment and use env_configuration argument if so
#     # if "TwoArm" in args.environment:
#     #     config["env_configuration"] = args.config
#     # else:
#     #     args.config = None

#     # Create dict to hold options that will be passed to env creation call
#     options = {}

#     # print welcome info
#     print("Welcome to robosuite v{}!".format(suite.__version__))
#     print(suite.__logo__)

#     # Choose environment and add it to options
#     options["env_name"] = choose_environment()

#     # If a multi-arm environment has been chosen, choose configuration and appropriate robot(s)
#     if "TwoArm" in options["env_name"]:
#         # Choose env config and add it to options
#         options["env_configuration"] = choose_multi_arm_config()

#         # If chosen configuration was bimanual, the corresponding robot must be Baxter. Else, have user choose robots
#         if options["env_configuration"] == "single-robot":
#             options["robots"] = choose_robots(exclude_bimanual=False, use_humanoids=True, exclude_single_arm=True)
#         else:
#             options["robots"] = []

#             # Have user choose two robots
#             for i in range(2):
#                 print("Please choose Robot {}...\n".format(i))
#                 options["robots"].append(choose_robots(exclude_bimanual=False, use_humanoids=True))
#     # If a humanoid environment has been chosen, choose humanoid robots
#     elif "Humanoid" in options["env_name"]:
#         options["robots"] = choose_robots(use_humanoids=True)
#     else:
#         options["robots"] = choose_robots(exclude_bimanual=False, use_humanoids=True)

#      # Get controller config
#     # controller_name = choose_controller()
#     # controller_config = load_composite_controller_config(
#     #     controller=controller_name,
#     #     robot=options["robots"][0],
#     #  )
#     # Get controller config
#     controller_config = load_composite_controller_config(
#         controller=args.controller,
#         robot=args.robots[0],
#     )
#     options["controller_configs"] = controller_config

#     # Available "camera" names = ('frontview', 'birdview', 'agentview', 'sideview', 'robot0_robotview', 'robot0_eye_in_hand').
#     # # Create environment
#     # env = suite.make(
#     #     **options,
#     #     has_renderer=True,
#     #     has_offscreen_renderer=False,
#     #     ignore_done=True,
#     #     use_camera_obs=False,
#     #     reward_shaping=True,
#     #     control_freq=20,
#     #     hard_reset=False,
#     #     renderer="mujoco",
#     # )
#     args.renderer = "mjviewer"

#     env = suite.make(
#         **options,
#         has_renderer=True,
#         has_offscreen_renderer=False,
#         render_camera=None,
#         ignore_done=True,
#         use_camera_obs=False,
#         control_freq=20,
#         renderer=args.renderer,
#     )


#     # Wrap this environment in a visualization wrapper
#     env = VisualizationWrapper(env, indicator_configs=None)

#     # Set up multiple camera views
#     # camera_names = ["frontview", "birdview", "agentview", "robot0_robotview", "robot0_eye_in_hand"]
#     # env.viewer.set_camera(camera_name=camera_names)

#     # Setup printing options for numbers
#     np.set_printoptions(formatter={"float": lambda x: "{0:0.3f}".format(x)})

#     # initialize device
#     if args.device == "keyboard":
#         from robosuite.devices import Keyboard

#         device = Keyboard(
#             env=env,
#             pos_sensitivity=args.pos_sensitivity,
#             rot_sensitivity=args.rot_sensitivity,
#         )
#         env.viewer.add_keypress_callback(device.on_press)
#     elif args.device == "spacemouse":
#         from robosuite.devices import SpaceMouse

#         device = SpaceMouse(
#             env=env,
#             pos_sensitivity=args.pos_sensitivity,
#             rot_sensitivity=args.rot_sensitivity,
#         )
#     elif args.device == "dualsense":
#         from robosuite.devices import DualSense

#         device = DualSense(
#             env=env,
#             pos_sensitivity=args.pos_sensitivity,
#             rot_sensitivity=args.rot_sensitivity,
#             reverse_xy=args.reverse_xy,
#         )
#     elif args.device == "mjgui":
#         from robosuite.devices.mjgui import MJGUI

#         device = MJGUI(env=env)
#     else:
#         raise Exception("Invalid device choice: choose either 'keyboard', 'dualsene' or 'spacemouse'.")

#     while True:
#         # Reset the environment
#         obs = env.reset()

#         # Setup rendering
#         cam_id = 0
#         num_cam = len(env.sim.model.camera_names)
#         env.render()

#         # Initialize variables that should the maintained between resets
#         last_grasp = 0

#         # Initialize device control
#         device.start_control()
#         all_prev_gripper_actions = [
#             {
#                 f"{robot_arm}_gripper": np.repeat([0], robot.gripper[robot_arm].dof)
#                 for robot_arm in robot.arms
#                 if robot.gripper[robot_arm].dof > 0
#             }
#             for robot in env.robots
#         ]

#         # Loop until we get a reset from the input or the task completes
#         while True:
#             start = time.time()

#             # Set active robot
#             active_robot = env.robots[device.active_robot]

#             # Get the newest action
#             input_ac_dict = device.input2action()

#             # If action is none, then this a reset so we should break
#             if input_ac_dict is None:
#                 break

#             from copy import deepcopy

#             action_dict = deepcopy(input_ac_dict)  # {}
#             # set arm actions
#             for arm in active_robot.arms:
#                 if isinstance(active_robot.composite_controller, WholeBody):  # input type passed to joint_action_policy
#                     controller_input_type = active_robot.composite_controller.joint_action_policy.input_type
#                 else:
#                     controller_input_type = active_robot.part_controllers[arm].input_type

#                 if controller_input_type == "delta":
#                     action_dict[arm] = input_ac_dict[f"{arm}_delta"]
#                 elif controller_input_type == "absolute":
#                     action_dict[arm] = input_ac_dict[f"{arm}_abs"]
#                 else:
#                     raise ValueError

#             # Maintain gripper state for each robot but only update the active robot with action
#             env_action = [robot.create_action_vector(all_prev_gripper_actions[i]) for i, robot in enumerate(env.robots)]
#             env_action[device.active_robot] = active_robot.create_action_vector(action_dict)
#             env_action = np.concatenate(env_action)
#             for gripper_ac in all_prev_gripper_actions[device.active_robot]:
#                 all_prev_gripper_actions[device.active_robot][gripper_ac] = action_dict[gripper_ac]

#             # ========== ADDED CODE ==========
#             # Get the ID of the 'frontview' camera
#             cam_id = env.sim.model.camera_name2id('frontview')

#             # Get the camera's position and rotation matrix
#             cam_pos = env.sim.data.cam_xpos[cam_id]
#             cam_rot = env.sim.data.cam_xmat[cam_id].reshape(3, 3)

#             print("Camera Position:", cam_pos)
#             print("Camera Rotation Matrix:\n", cam_rot)

#             # Get the robot's joint angles
#             joint_angles = env.robots[0]._joint_positions
#             print("Robot Joint Angles:", joint_angles)
#             # ===============================

#             env.step(env_action)
#             env.render()

#             # limit frame rate if necessary
#             if args.max_fr is not None:
#                 elapsed = time.time() - start
#                 diff = 1 / args.max_fr - elapsed
#                 if diff > 0:
#                     time.sleep(diff)
import argparse
import time
import numpy as np
import robosuite as suite
from robosuite import load_composite_controller_config
from robosuite.controllers.composite.composite_controller import WholeBody
from robosuite.wrappers import VisualizationWrapper
from robosuite.utils.input_utils import *
from copy import deepcopy
import pickle
import datetime

# New function to save collected data
def save_trajectory(data, folder="trajectories"):
    """
    Saves the collected trajectory data to a file.
    """
    import os
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(folder, f"trajectory_{timestamp}.pkl")
    
    with open(filename, "wb") as f:
        pickle.dump(data, f)
    print(f"Trajectory saved to {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", type=str, default="Lift")
    parser.add_argument("--robots", nargs="+", type=str, default="Panda", help="Which robot(s) to use in the env")
    parser.add_argument("--device", type=str, default="keyboard")
    parser.add_argument("--pos-sensitivity", type=float, default=1.5, help="How much to scale position user inputs")
    parser.add_argument("--rot-sensitivity", type=float, default=1.5, help="How much to scale rotation user inputs")
    args = parser.parse_args()

    # --- VLA Data Collection Setup ---
    VLA_CAMERA_NAME = "agentview"
    LANGUAGE_INSTRUCTION = "lift the red cube"

    options = {}
    options["env_name"] = args.environment
    options["robots"] = args.robots
    
    controller_config = load_composite_controller_config(controller=None, robot=args.robots[0])

    env = suite.make(
        **options,
        has_renderer=True,
        has_offscreen_renderer=True,
        ignore_done=True,
        use_camera_obs=True,
        camera_names=VLA_CAMERA_NAME,
        camera_heights=84,
        camera_widths=84,
        control_freq=20,
        controller_configs=controller_config,
    )
    
    env = VisualizationWrapper(env, indicator_configs=None)
    np.set_printoptions(formatter={"float": lambda x: "{0:0.3f}".format(x)})

    # Initialize device
    if args.device == "keyboard":
        from robosuite.devices import Keyboard
        device = Keyboard(env=env, pos_sensitivity=args.pos_sensitivity, rot_sensitivity=args.rot_sensitivity)
        env.viewer.add_keypress_callback(device.on_press)
    else:
        raise Exception("This script is configured for keyboard control.")

    while True:
        obs = env.reset()
        episode_data = []
        env.render()

        # Initialize variables that should be maintained between resets
        last_grasp = 0
        device.start_control()
        
        all_prev_gripper_actions = [
            {
                f"{robot_arm}_gripper": np.repeat([0], robot.gripper[robot_arm].dof)
                for robot_arm in robot.arms
                if robot.gripper[robot_arm].dof > 0
            }
            for robot in env.robots
        ]
        
        while True:
            start = time.time()

            # Set active robot
            active_robot = env.robots[device.active_robot]

            # Get the newest action using the correct method
            input_ac_dict = device.input2action()

            # If action is none, then this a reset so we should break
            if input_ac_dict is None:
                if episode_data:
                    save_trajectory(episode_data)
                break

            action_dict = deepcopy(input_ac_dict)
            
            # set arm actions
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
                    raise ValueError

            # Maintain gripper state for each robot but only update the active robot with action
            env_action = [robot.create_action_vector(all_prev_gripper_actions[i]) for i, robot in enumerate(env.robots)]
            env_action[device.active_robot] = active_robot.create_action_vector(action_dict)
            env_action = np.concatenate(env_action)
            
            for gripper_ac in all_prev_gripper_actions[device.active_robot]:
                all_prev_gripper_actions[device.active_robot][gripper_ac] = action_dict[gripper_ac]

            # Step through the environment
            obs, reward, done, info = env.step(env_action)
            
            # --- CAPTURE DATA FOR VLA AT EACH TIMESTEP ---
            timestep_data = {
                'vision': obs[f'{VLA_CAMERA_NAME}_image'],
                'proprioception': {
                    'joint_positions': obs['robot0_joint_pos'],
                    'joint_velocities': obs['robot0_joint_vel'],
                    'eef_position': obs['robot0_eef_pos'],
                    'eef_quaternion': obs['robot0_eef_quat'],
                    'gripper_state': obs['robot0_gripper_qpos'],
                },
                'action': env_action,
                'language_instruction': LANGUAGE_INSTRUCTION,
            }
            episode_data.append(timestep_data)

            env.render()

            # limit frame rate if necessary
            elapsed = time.time() - start
            diff = 1 / 20 - elapsed  # 20 fps
            if diff > 0:
                time.sleep(diff)