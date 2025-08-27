"""
SO101 gripper with single moving jaw.
"""
import numpy as np

from robosuite.models.grippers.gripper_model import GripperModel
from robosuite.utils.mjcf_utils import xml_path_completion


class SO101Gripper(GripperModel):
    """
    SO101 gripper with a single moving jaw. The gripper uses a fixed part as one finger
    and has a moving jaw as the second finger.

    Args:
        idn (int or str): Number or some other unique identification string for this gripper instance
    """

    def __init__(self, idn=0):
        super().__init__(xml_path_completion("grippers/so101_gripper.xml"), idn=idn)

    def format_action(self, action):
        """
        Maps continuous action into gripper position command.
        
        Args:
            action (np.array): gripper-specific action
            
        Returns:
            np.array: Command to be sent to gripper
        """
        assert len(action) == self.dof
        # Map [-1, 1] directly to open/close
        if action[0] > 0:  # Close gripper
            self.current_action = np.array([1.0])
        else:  # Open gripper
            self.current_action = np.array([-1.0])
        return self.current_action

    @property
    def init_qpos(self):
        """
        Initial position for gripper joint.
        """
        return np.array([0.0])  # Start at neutral position

    @property
    def speed(self):
        """
        Speed of the gripper joints.
        """
        return 0.2

    @property
    def _important_geoms(self):
        """
        Define important geoms for the gripper.
        """
        return {
            "left_finger": ["moving_jaw_collision"],  # Moving jaw
            "right_finger": ["fixed_jaw_collision"],  # Fixed part
            "left_fingerpad": ["moving_jaw_collision"],  # Contact surface of moving jaw
            "right_fingerpad": ["fixed_jaw_collision"]  # Contact surface of fixed part
        }