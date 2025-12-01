import torch

from isaaclab.devices.retargeter_base import RetargeterBase, RetargeterCfg

from geort import load_model


class AllegroHandRetargeterCfg(RetargeterCfg):
    def __init__(self, hand_side: str, ckpt_tag: str, sim_device: str):
        super().__init__()
        self.hand_side = hand_side
        self.ckpt_tag = ckpt_tag
        self.sim_device = sim_device

class AllegroHandRetargeter(RetargeterBase):
    def __init__(self, cfg: AllegroHandRetargeterCfg):
        super().__init__(cfg)
        self.hand_side = cfg.hand_side
        self.model = load_model(cfg.ckpt_tag)

    def retarget(self, mocap_result: dict) -> torch.Tensor:
        human_relative_joint_positions = mocap_result.get("relative_joint_positions")
        robot_joint_pos_targets = self.model.forward(human_relative_joint_positions)
        return torch.tensor(
            robot_joint_pos_targets,
            dtype=torch.float32,
            device=self._sim_device,
        )
