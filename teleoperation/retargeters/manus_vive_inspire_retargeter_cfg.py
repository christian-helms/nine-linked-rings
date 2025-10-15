"""Retargeter configuration for ManusVive to RM75 + Inspire dexterous hand."""

from __future__ import annotations

import numpy as np
import torch

from isaaclab.devices.retargeter_base import RetargeterBase, RetargeterCfg
from isaaclab.controllers import DifferentialIKControllerCfg, DifferentialIKController
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils import configclass
from isaaclab.scene import InteractiveScene

class TaskSpaceController:

    def __init__(self, scene: InteractiveScene):
        self.scene = scene
        self.robot_entity_cfg = SceneEntityCfg("robot", joint_names=["joint_[1-7]"], body_names=["ee_link"])
        self.robot_entity_cfg.resolve(scene)

    def get_command(self, hand_data: dict) -> np.ndarray:
        pass

@configclass
class ManusViveInspireRetargeterCfg(RetargeterCfg):
    """Configuration for ManusVive to Inspire hand retargeting."""

    # Scale factors for position and rotation
    pos_scale: float = 1.0
    rot_scale: float = 1.0

    # Offset from wrist tracking to robot base
    wrist_offset: tuple[float, float, float] = (0.0, 0.0, 0.0)

    # Joint mapping scale factors (Manus to Inspire)
    # Manus joints are in radians, Inspire expects radians
    finger_scale: float = 1.0

    # Smoothing factor for finger joints (0.0 = no smoothing, 1.0 = max smoothing)
    smoothing: float = 0.3


class ManusViveInspireRetargeter(RetargeterBase):
    """Retargeter from ManusVive hand tracking to RM75 Inspire dexterous hand.

    This retargeter converts full hand tracking data from ManusVive (with Vive trackers for absolute positions)
    into control commands for the Inspire hand attached onto the RM75 robotic arm.

    The whole system has the following joints:
    - Arm: 7 DOF (joint_1 to joint_7)
    - Thumb: 4 DOF (yaw, pitch, intermediate, distal)
    - Index, Middle, Ring, Pinky: 2 DOF each (proximal, intermediate)

    Total: 7 (arm) + 12 (hand) = 19 DOF
    """

    cfg: ManusViveInspireRetargeterCfg

    def __init__(self, cfg: ManusViveInspireRetargeterCfg):
        """Initialize the retargeter.

        Args:
            cfg: Configuration for the retargeter.
        """
        super().__init__(cfg)
        self.cfg = cfg
        self._wrist_offset = np.array(self.cfg.wrist_offset, dtype=np.float32)

        # Previous finger states for smoothing
        self._prev_finger_state = np.zeros(12, dtype=np.float32)

        self

    def retarget(self, raw_data: dict) -> "torch.Tensor":
        """Convert ManusVive tracking data to robot commands.

        Args:
            raw_data: Dictionary containing hand tracking data with keys:
                - 'HAND_RIGHT' or 'HAND_LEFT': Dictionary of joint data
                - Finger joints: flex angles for each finger segment

        Returns:
            numpy.ndarray: Control command with 19 elements:
                - [0:7]: Arm joint positions (computed from hand pose)
                - [7:19]: Hand joint positions (12 DOF):
                    - [7:11]: Thumb (yaw, pitch, intermediate, distal)
                    - [11:13]: Index (proximal, intermediate)
                    - [13:15]: Middle (proximal, intermediate)
                    - [15:17]: Ring (proximal, intermediate)
                    - [17:19]: Pinky (proximal, intermediate)
        """
        from isaaclab.devices.openxr.openxr_device import OpenXRDevice

        # Get right hand data (for controlling the robot)
        hand_data = raw_data.get(OpenXRDevice.TrackingTarget.HAND_RIGHT, {})

        if not hand_data:
            # Return zero command if no valid data
            return torch.zeros(19, dtype=torch.float32, device=self._sim_device)

        # Initialize command array: 7 arm + 12 hand joints
        command = np.zeros(19, dtype=np.float32)

        # === Arm Control (SE3 from hand pose) ===
        # For now, we'll compute arm IK from hand position/orientation
        # This is simplified - in production, you'd use proper IK
        if "palm" in hand_data:
            # palm_pose = hand_data["palm"]
            # position = palm_pose[:3] * self.cfg.pos_scale
            # orientation = palm_pose[3:]  # qw, qx, qy, qz

            # For teleoperation, we'll output delta pose for IK controller
            # For direct control, you'd need IK here
            # For now, keep arm in neutral pose and only control hand
            command[0:7] = [0.0, 0.0, 0.0, 1.57, 0.0, 0.0, 0.0]

        # === Hand Control (Direct Joint Mapping) ===
        finger_joints = self._extract_finger_joints(hand_data)

        # Apply smoothing
        if self.cfg.smoothing > 0.0:
            alpha = self.cfg.smoothing
            finger_joints = alpha * self._prev_finger_state + (1.0 - alpha) * finger_joints
            self._prev_finger_state = finger_joints

        # Map to Inspire hand joints
        command[7:19] = finger_joints

        # Convert to torch tensor for compatibility with DeviceBase
        return torch.tensor(command, dtype=torch.float32, device=self._sim_device)

    def _extract_finger_joints(self, hand_data: dict) -> np.ndarray:
        """Extract and map finger joint angles from Manus hand data.

        Args:
            hand_data: Dictionary of hand tracking data from Manus gloves

        Returns:
            numpy.ndarray: 12-element array of finger joint positions
        """
        finger_joints = np.zeros(12, dtype=np.float32)

        # Manus provides joint angles for each finger segment
        # The exact key names depend on the Manus SDK version
        # Common names: thumb_cmc, thumb_mcp, thumb_ip, thumb_tip
        # finger_mcp, finger_pip, finger_dip, finger_tip

        # === Thumb (4 DOF) ===
        # Inspire: thumb_proximal_yaw_joint, thumb_proximal_pitch_joint,
        #          thumb_intermediate_joint, thumb_distal_joint
        if "thumb" in hand_data:
            thumb_data = hand_data["thumb"]
            # CMC joint -> yaw and pitch
            finger_joints[0] = self._get_flex_angle(thumb_data, "cmc_spread", 0.0) * self.cfg.finger_scale
            finger_joints[1] = self._get_flex_angle(thumb_data, "cmc_flex", 0.0) * self.cfg.finger_scale
            # MCP joint -> intermediate
            finger_joints[2] = self._get_flex_angle(thumb_data, "mcp", 0.0) * self.cfg.finger_scale
            # IP joint -> distal
            finger_joints[3] = self._get_flex_angle(thumb_data, "ip", 0.0) * self.cfg.finger_scale

        # === Index Finger (2 DOF) ===
        if "index" in hand_data:
            index_data = hand_data["index"]
            finger_joints[4] = self._get_flex_angle(index_data, "mcp", 0.0) * self.cfg.finger_scale
            finger_joints[5] = self._get_flex_angle(index_data, "pip", 0.0) * self.cfg.finger_scale

        # === Middle Finger (2 DOF) ===
        if "middle" in hand_data:
            middle_data = hand_data["middle"]
            finger_joints[6] = self._get_flex_angle(middle_data, "mcp", 0.0) * self.cfg.finger_scale
            finger_joints[7] = self._get_flex_angle(middle_data, "pip", 0.0) * self.cfg.finger_scale

        # === Ring Finger (2 DOF) ===
        if "ring" in hand_data:
            ring_data = hand_data["ring"]
            finger_joints[8] = self._get_flex_angle(ring_data, "mcp", 0.0) * self.cfg.finger_scale
            finger_joints[9] = self._get_flex_angle(ring_data, "pip", 0.0) * self.cfg.finger_scale

        # === Pinky Finger (2 DOF) ===
        if "pinky" in hand_data:
            pinky_data = hand_data["pinky"]
            finger_joints[10] = self._get_flex_angle(pinky_data, "mcp", 0.0) * self.cfg.finger_scale
            finger_joints[11] = self._get_flex_angle(pinky_data, "pip", 0.0) * self.cfg.finger_scale

        # Ensure all angles are within valid ranges
        # Inspire hand joints are typically 0 to ~90 degrees (0 to 1.57 radians)
        finger_joints = np.clip(finger_joints, 0.0, 1.47)  # ~84 degrees max

        return finger_joints

    def _get_flex_angle(self, finger_data: dict, joint_name: str, default: float = 0.0) -> float:
        """Extract flex angle for a specific joint.

        Args:
            finger_data: Dictionary containing finger joint data
            joint_name: Name of the joint to extract
            default: Default value if joint not found

        Returns:
            float: Flex angle in radians
        """
        if isinstance(finger_data, dict):
            return finger_data.get(joint_name, default)
        else:
            # If finger_data is directly a value (some SDK versions)
            return finger_data if finger_data is not None else default

    def get_joint_names(self) -> list[str]:
        """Get the names of all controlled joints in order.

        Returns:
            list[str]: List of joint names matching the output command array
        """
        return [
            # Arm joints
            "joint_1",
            "joint_2",
            "joint_3",
            "joint_4",
            "joint_5",
            "joint_6",
            "joint_7",
            # Hand joints
            "thumb_proximal_yaw_joint",
            "thumb_proximal_pitch_joint",
            "thumb_intermediate_joint",
            "thumb_distal_joint",
            "index_proximal_joint",
            "index_intermediate_joint",
            "middle_proximal_joint",
            "middle_intermediate_joint",
            "ring_proximal_joint",
            "ring_intermediate_joint",
            "pinky_proximal_joint",
            "pinky_intermediate_joint",
        ]

