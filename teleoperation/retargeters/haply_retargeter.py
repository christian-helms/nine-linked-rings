import torch

from isaaclab.utils.math import (
    quat_mul,
)


class HaplyRetargeter:
    def __init__(self, ee_start_position: torch.Tensor):
        self.neutral_pose_is_set = False
        self.ee_start_position = ee_start_position
        self.transform_quat = torch.tensor([0.0, -0.7071068, 0.0, 0.7071068])

    def set_haply_start_position(self, haply_start_position: torch.Tensor) -> None:
        self.haply_start_position = haply_start_position

    def retarget(self, command: torch.Tensor) -> torch.Tensor:
        command_pos = command[:3] - self.haply_start_position
        command_pos = self.ee_start_position + command_pos
        command_quat = torch.tensor([command[6], -command[5], -command[3], command[4]])
        return torch.cat([command_pos, command_quat, command[7:]], dim=0)
