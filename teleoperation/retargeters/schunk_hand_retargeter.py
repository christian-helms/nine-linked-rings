import torch
import numpy as np
from pathlib import Path
from typing import Any, Optional, cast

import dex_retargeting.robot_wrapper as robot_wrapper_module
from dex_retargeting.retargeting_config import RetargetingConfig
from mediapipe.python.solutions.hands import HandLandmark
from isaaclab.devices.retargeter_base import RetargeterBase, RetargeterCfg
from isaaclab.devices.openxr.openxr_device import OpenXRDevice
from teleoperation.retargeters.utils import HAND_LANDMARK_TO_MANUS


from dex_retargeting.constants import (
    RobotName,
    RetargetingType,
    HandType,
    get_default_config_path,
)

from rich.pretty import pprint

LEFT = OpenXRDevice.TrackingTarget.HAND_LEFT
RIGHT = OpenXRDevice.TrackingTarget.HAND_RIGHT


def _ensure_robot_wrapper_patch():
    """Avoid accessing pinocchio's std::vector bindings unavailable in Isaac Sim."""

    wrapper_cls = cast(Any, robot_wrapper_module.RobotWrapper)
    if getattr(wrapper_cls, "_isaac_pin_fallback_ready", False):
        return

    original_init = wrapper_cls.__init__

    def _patched_init(self, urdf_path, *args, **kwargs):
        original_init(self, urdf_path, *args, **kwargs)
        self._isaac_pin_urdf_path = str(urdf_path)
        self._isaac_pin_joint_cache = None

    def _load_joint_cache(self):
        cache = getattr(self, "_isaac_pin_joint_cache", None)
        if cache is not None:
            return cache

        from dex_retargeting import yourdfpy as urdf

        urdf_data = urdf.URDF.load(self._isaac_pin_urdf_path)
        name_to_indices: dict[str, list[int]] = {}
        for name, joint in urdf_data.joint_map.items():
            joint_type = getattr(joint, "type", None)
            if joint_type == "fixed" or not name:
                continue
            try:
                joint_id = self.model.getJointId(name)
            except Exception:
                continue
            joint_model = self.model.joints[joint_id]
            nq = getattr(joint_model, "nq", 0)
            if nq <= 0:
                continue
            idx_start = joint_model.idx_q
            name_to_indices[name] = [idx_start + offset for offset in range(nq)]

        total_dof = int(getattr(self.model, "nq", 0))
        dof_names: list[Optional[str]] = [None] * total_dof
        for joint_name, indices in name_to_indices.items():
            for idx in indices:
                if 0 <= idx < total_dof:
                    dof_names[idx] = joint_name

        for idx, value in enumerate(dof_names):
            if value is None:
                dof_names[idx] = f"unknown_joint_{idx}"

        cache = (name_to_indices, tuple(cast(str, name) for name in dof_names))
        self._isaac_pin_joint_cache = cache
        return cache

    def _safe_dof_joint_names(self):
        _, dof_names = _load_joint_cache(self)
        return list(dof_names)

    def _safe_joint_names(self):
        name_to_indices, _ = _load_joint_cache(self)
        ordered = sorted(
            (
                (indices[0], joint_name)
                for joint_name, indices in name_to_indices.items()
            ),
            key=lambda item: item[0],
        )
        return [name for _, name in ordered]

    def _safe_get_joint_index(self, name: str):
        name_to_indices, _ = _load_joint_cache(self)
        if name not in name_to_indices:
            raise ValueError(f"Joint {name} given does not appear to be in robot XML.")
        return name_to_indices[name][0]

    setattr(wrapper_cls, "__init__", _patched_init)
    setattr(wrapper_cls, "dof_joint_names", property(_safe_dof_joint_names))
    setattr(wrapper_cls, "joint_names", property(_safe_joint_names))
    setattr(wrapper_cls, "get_joint_index", _safe_get_joint_index)
    setattr(wrapper_cls, "_isaac_pin_fallback_ready", True)


class SchunkHandRetargeterCfg(RetargeterCfg):
    def __init__(self, hand_side: str, joint_names: list[str]):
        super().__init__()
        if hand_side not in ["left", "right"]:
            raise ValueError(
                f"Invalid hand side: {hand_side}. Must be 'left' or 'right'."
            )
        self.hand_side = LEFT if hand_side == "left" else RIGHT
        self.joint_names = joint_names


class SchunkHandRetargeter(RetargeterBase):
    def __init__(self, cfg: SchunkHandRetargeterCfg):
        super().__init__(cfg)
        self.hand_side = cfg.hand_side

        _ensure_robot_wrapper_patch()

        config_path = get_default_config_path(
            RobotName.svh,
            RetargetingType.dexpilot,
            HandType.left if self.hand_side == LEFT else HandType.right,
        )
        robot_dir = (
            Path(__file__).absolute().parent.parent.parent
            / "dex-urdf"
            / "robots"
            / "hands"
        )
        RetargetingConfig.set_default_urdf_dir(str(robot_dir))

        self.retargeter = RetargetingConfig.load_from_file(str(config_path)).build()

        self.hand_joint_pos = np.zeros((21, 3))

        self.joint_indices = np.array(
            [
                self.retargeter.joint_names.index(
                    name.replace("Left_Hand_", "left_hand_")
                    if self.hand_side == LEFT
                    else name.replace("Right_Hand_", "right_hand_")
                )
                for name in cfg.joint_names
            ]
        )

        ### DEBUG ###
        print('rtype:', self.retargeter.optimizer.retargeting_type)
        print('adaptor:', type(getattr(self.retargeter.optimizer, 'adaptor', None)))
        print("DEBUG DONE")

    def retarget(self, skeleton_data: dict) -> torch.Tensor:
        """
        Args:
            skeleton_data: dict of the following structure
                <TrackingTarget.HAND_LEFT: 0>: {
                    'palm': array([0., 0., 0., 1., 0., 0., 0.], dtype=float32),
                    'wrist': array([0., 0., 0., 1., 0., 0., 0.], dtype=float32),
                    'thumb_metacarpal': array([0., 0., 0., 1., 0., 0., 0.], dtype=float32),
                    'thumb_proximal': ...,
                    'thumb_distal': ...,
                    'thumb_tip': ...,
                    'index_metacarpal': ...,
                    'index_proximal': ...,
                    'index_intermediate': ...,
                    'index_distal': ..,
                    'index_tip': ...,
                    ...
                    'middle_metacarpal': ...,
                    ...
                    'ring_metacarpal': ...,
                    ...
                    'little_metacarpal': ...,
                ...}
                <TrackingTarget.HAND_RIGHT: 1>: ...
                <TrackingTarget.HEAD: 2>: array([0., 0., 0., 1., 0., 0., 0.], dtype=float32)}

            Returns:
        """

        hand_data = skeleton_data[self.hand_side]

        # Dex retargeting uses hand joint ordering/format as specified in HandLandmark
        for enum_value in HandLandmark:
            self.hand_joint_pos[enum_value] = hand_data[
                HAND_LANDMARK_TO_MANUS[enum_value]
            ][:3]
        indices = self.retargeter.optimizer.target_link_human_indices
        ref_value = (
            self.hand_joint_pos[indices[1, :], :]
            - self.hand_joint_pos[indices[0, :], :]
        )
        qpos = self.retargeter.retarget(ref_value)
        relevant_qpos = qpos[self.joint_indices]

        print("qpos: ", qpos)
        print("ref_value norm: ", torch.linalg.norm(torch.from_numpy(ref_value), dim=1))

        return torch.tensor(relevant_qpos, dtype=torch.float32, device=self._sim_device)
