import torch

from isaaclab.devices.retargeter_base import RetargeterBase, RetargeterCfg
from isaaclab.devices.openxr.openxr_device import OpenXRDevice
from isaaclab.utils.math import subtract_frame_transforms


class WristRetargeterCfg(RetargeterCfg):
    def __init__(self, hand_side: str):
        super().__init__()
        if hand_side not in ["left", "right"]:
            raise ValueError(
                f"Invalid hand side: {hand_side}. Must be 'left' or 'right'."
            )
        self.hand_side = (
            OpenXRDevice.TrackingTarget.HAND_LEFT
            if hand_side == "left"
            else OpenXRDevice.TrackingTarget.HAND_RIGHT
        )


class WristRetargeter(RetargeterBase):
    def __init__(self, cfg: WristRetargeterCfg):
        super().__init__(cfg)
        self.hand_side = cfg.hand_side

    def set_origin_pos(self, pos: torch.Tensor) -> None:
        """The retargeted pose is relative to this pose."""
        self.origin_pos = pos

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

        wrist_pose = torch.tensor(hand_data.get("wrist"), dtype=torch.float32)

        if not hasattr(self, "origin_pos"):
            # query during calibration
            return wrist_pose.to(self._sim_device)

        retargeted_pos = wrist_pose[:3] - self.origin_pos

        return torch.cat([retargeted_pos, wrist_pose[3:]], dim=0).to(self._sim_device)
