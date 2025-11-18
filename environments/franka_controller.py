import torch

from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg
from isaaclab.scene.interactive_scene import InteractiveScene
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils.math import subtract_frame_transforms


class FrankaController:
    def __init__(self, use_relative_mode: bool, ik_method, scene: InteractiveScene):
        super().__init__()
        cfg = DifferentialIKControllerCfg(
            command_type="pose", use_relative_mode=use_relative_mode, ik_method=ik_method
        )
        self.controller = DifferentialIKController(
            cfg=cfg, num_envs=scene.num_envs, device=scene.device
        )
        self.scene = scene
        self.robot = self.scene["robot"]
        self.robot_entity_cfg = SceneEntityCfg(
            "robot", joint_names=["panda_joint.*"], body_names=["panda_hand"]
        )
        self.robot_entity_cfg.resolve(self.scene)

        if self.robot.is_fixed_base:
            self.ee_jacobi_idx = self.robot_entity_cfg.body_ids[0] - 1  # pyright: ignore[reportIndexIssue]
        else:
            self.ee_jacobi_idx = self.robot_entity_cfg.body_ids[0]  # pyright: ignore[reportIndexIssue]
        self.ee_body_id = self.robot_entity_cfg.body_ids[0]  # pyright: ignore[reportIndexIssue]
        self.joint_ids = self.robot_entity_cfg.joint_ids

    def retarget(self, wrist_pose_target_b: torch.Tensor) -> torch.Tensor:
        """Computes joint position targets to achieve the given wrist pose.

           Frame abbbreviations:
            - w: world_frame
            - b: base frame
          Args:
            - wrist_pose_b: shape (N, 7) 
              - N: number of environments
              - wrist_pose_b[:, :3]: position (xyz) in robot's base frame
              - wrist_pose_b[:, 3:7]: orientation quaternion (w, x, y, z) in robot's base frame
           
          Returns:
            - joint_pos_targets: shape (N, 7) (the franka has 7 joints)
        """
        jacobian = self.robot.root_physx_view.get_jacobians()[
            :, self.ee_jacobi_idx, :, self.joint_ids
        ]
        ee_pose_w = self.robot.data.body_pose_w[:, self.ee_body_id]
        root_pose_w = self.robot.data.root_pose_w
        joint_pos = self.robot.data.joint_pos[:, self.joint_ids]

        ee_pos_b, ee_quat_b = subtract_frame_transforms(
            root_pose_w[:, 0:3],
            root_pose_w[:, 3:7],
            ee_pose_w[:, 0:3],
            ee_pose_w[:, 3:7],
        )

        self.controller.set_command(wrist_pose_target_b)
        joint_pos_targets = self.controller.compute(
            ee_pos_b, ee_quat_b, jacobian, joint_pos
        )

        return joint_pos_targets
