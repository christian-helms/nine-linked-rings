import torch

from isaaclab.devices.retargeter_base import RetargeterBase, RetargeterCfg

from isaaclab.utils.math import (
    quat_mul,
    subtract_frame_transforms,
)


class WristRetargeterCfg(RetargeterCfg):
    def __init__(self, hand_side: str, sim_device: str):
        super().__init__()
        self.hand_side = hand_side
        self.sim_device = sim_device


class WristRetargeter(RetargeterBase):
    def __init__(self, cfg: WristRetargeterCfg):
        super().__init__(cfg)
        self.hand_side = cfg.hand_side
        self.eTn = torch.tensor(
            [  # see the note in self.retarget() for the meaning of this matrix
                [1, 0, 0, 0],
                [0, 0, -1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
            ],
            dtype=torch.float32,
            device=self._sim_device,
        )
        self.neutral_pose_is_set = False

    def set_ee_start_pose(self, pose: tuple[torch.Tensor, torch.Tensor]) -> None:
        self.ee_start_pos = pose[0].squeeze(0).to(self._sim_device)
        self.ee_start_quat = pose[1].squeeze(0).to(self._sim_device)

    def set_neutral_pose(self, pose: torch.Tensor) -> None:
        """The retargeted pose is relative to this pose."""
        self.neutral_pose = pose
        self.neutral_pose_is_set = True

    def retarget(self, mocap_result: dict) -> torch.Tensor:
        """There are 4 frames involved in the retargeting:
        - o: origin tracker frame
        - n: neutral hand pose frame
        - e: end effector frame
        - p: pose frame

        By aTb we denote the homogeneous transformation matrix mapping points in coordinate frame b to a.

        We want to output eTp (in translation + quaternion form) and we know:
        - oTn (self.neutral_pose)
        - oTp (mocap_result.get("wrist_pos"), mocap_result.get("wrist_quat"))
        - eTn (defined in the constructor)

        So we can compute eTp as eTp = eTn * nTo * oTp and then convert to translation + quaternion form.
        """
        wrist_pos = torch.tensor(
            mocap_result.get("wrist_pos"), dtype=torch.float32, device=self._sim_device
        )
        wrist_quat = torch.tensor(
            mocap_result.get("wrist_quat"), dtype=torch.float32, device=self._sim_device
        )

        if not self.neutral_pose_is_set:
            return torch.cat([wrist_pos, wrist_quat], dim=0)

        pos_delta = wrist_pos - self.neutral_pose[:3]
        pos_delta = self.eTn[:3, :3] @ pos_delta
        ee_goal_pos = self.ee_start_pos + pos_delta

        _, test_quat = subtract_frame_transforms(
            wrist_pos, wrist_quat, self.neutral_pose[:3], self.neutral_pose[3:]
        )
        quat_delta = torch.tensor(
            [test_quat[0], test_quat[2], -test_quat[1], -test_quat[3]],
            dtype=torch.float32,
            device=self._sim_device,
        )
        ee_goal_quat = quat_mul(quat_delta, self.ee_start_quat)

        return torch.cat([ee_goal_pos, ee_goal_quat], dim=0)
