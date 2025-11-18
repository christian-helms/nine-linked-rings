import torch

from isaaclab.devices.retargeter_base import RetargeterBase, RetargeterCfg

class ORCAHandRetargeterCfg(RetargeterCfg):

    def __init__(self, hand_side: str):
        super().__init__()
        self.hand_side = hand_side

class ORCAHandRetargeter(RetargeterBase):

    def __init__(self, cfg: ORCAHandRetargeterCfg):
        super().__init__(cfg)
        self.hand_side = cfg.hand_side

    def retarget(self, skeleton_data: dict) -> torch.Tensor:
        return torch.tensor(skeleton_data[f"{self.hand_side}_wrist"])