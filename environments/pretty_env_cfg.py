# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Configuration for Nine Linked Rings environment with RM75+Inspire hand."""

from __future__ import annotations

if __name__ == "__main__":
    import argparse
    import torch

    from isaaclab.app import AppLauncher

    parser = argparse.ArgumentParser(description="Tutorial on creating a cartpole base environment.")
    parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to spawn.")
    AppLauncher.add_app_launcher_args(parser)
    args_cli = parser.parse_args()
    app_launcher = AppLauncher(args_cli)
    simulation_app = app_launcher.app


import isaaclab.envs.mdp as mdp
import isaaclab.sim as sim_utils
from assets.assemblies_cfg import get_svh_left_cfg
from isaaclab.assets import AssetBaseCfg
from isaaclab.controllers import DifferentialIKControllerCfg
from isaaclab.envs import ManagerBasedEnv, ManagerBasedEnvCfg
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR


@configclass
class NineLinkedRingsSceneCfg(InteractiveSceneCfg):
    """Configuration for the Nine Linked Rings scene."""

    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.UsdFileCfg(
            usd_path="./assets/ground_plane/ground_plane.usda",
        ),
    )

    dome_light = AssetBaseCfg(
        prim_path="/World/DomeLight",
        spawn=sim_utils.DomeLightCfg(color=(0.9, 0.9, 0.9), intensity=500.0),
    )
    distant_light = AssetBaseCfg(
        prim_path="/World/DistantLight",
        spawn=sim_utils.DistantLightCfg(intensity=3000.0, angle=0.25),
        init_state=AssetBaseCfg.InitialStateCfg(rot=(0.738, 0.477, 0.477, 0.0)),
    )

    puzzle = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/NineLinkedRings",
        spawn=sim_utils.UsdFileCfg(
            usd_path="./assets/nine_linked_rings/nine_linked_rings.usda",
            scale=(0.15, 0.15, 0.15),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=(0.55, -0.3, 0.7),  # Position in front of robot
            rot=(0.7071, 0.0, 0.0, 0.7071),
        ),
    )

    robot = get_svh_left_cfg()

    ee_start = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/ee_start",
        spawn=sim_utils.UsdFileCfg(
            usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/UIElements/frame_prim.usd",
            scale=(0.001, 0.001, 0.001),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=(0.1952, 0.0, 0.65274),
            rot=(-0.27240371, -0.65212406, -0.27199824, -0.65310595),
        ),
    )


@configclass
class ObservationsCfg:
    """Observation specifications for the environment."""

    pass


@configclass
class ActionsCfg:
    """Action specifications for the environment."""

    arm_action = mdp.actions.DifferentialInverseKinematicsActionCfg(
        asset_name="robot",
        joint_names=["panda_joint.*"],
        body_name="panda_hand",  # or left tower (need to try it out)
        scale=1.0,
        controller=DifferentialIKControllerCfg(
            command_type="pose",
            use_relative_mode=False,
            ik_method="pinv",
        ),
    )

    hand_action = mdp.actions.JointPositionActionCfg(
        asset_name="robot",
        joint_names=[
            "Left_Hand_Thumb_Opposition",
            "Left_Hand_Thumb_Flexion",
            "Left_Hand_Index_Finger_Proximal",
            "Left_Hand_Index_Finger_Distal",
            "Left_Hand_Middle_Finger_Proximal",
            "Left_Hand_Middle_Finger_Distal",
            "Left_Hand_Ring_Finger",
            "Left_Hand_Pinky",
            "Left_Hand_Finger_Spread",
        ],
        scale=1.0,
        use_default_offset=True,
    )


@configclass
class EventCfg:
    """Configuration for events."""

    reset_scene_defaults: EventTerm = EventTerm(
        func=mdp.reset_scene_to_default,
        mode="reset",
        params={"reset_joint_targets": True},
    )


@configclass
class NineLinkedRingsEnvCfg(ManagerBasedEnvCfg):
    """Configuration for the Nine Linked Rings environment."""

    seed: int = 1337

    scene: NineLinkedRingsSceneCfg = NineLinkedRingsSceneCfg(num_envs=1, env_spacing=2.5)

    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    events: EventCfg = EventCfg()

    def __post_init__(self):
        """Post initialization."""
        # Viewer settings
        self.viewer.eye = (1.2, 0.9, 1.3)
        self.viewer.lookat = (0.5, 0.0, 0.7)

        # Simulation settings
        self.decimation = 4
        self.sim.dt = 1.0 / 180.0
        self.sim.render_interval = 2
        self.sim.physics_material = sim_utils.RigidBodyMaterialCfg(
            static_friction=1.0,
            dynamic_friction=1.0,
            restitution=0.0,
        )

        # Episode length
        self.episode_length_s = 300.0  # 5 minutes for teleoperation


def main():
    env_cfg = NineLinkedRingsEnvCfg()
    env_cfg.scene.num_envs = args_cli.num_envs
    env_cfg.sim.device = args_cli.device
    env = ManagerBasedEnv(cfg=env_cfg)
    print(env.step_dt)
    print(env.physics_dt)

    count = 0
    env.reset()
    while simulation_app.is_running():
        with torch.inference_mode():
            ee_goal_transl, ee_goal_quat = env.scene["ee_start"].get_local_poses()
            action = torch.cat((ee_goal_transl, ee_goal_quat), dim=1)
            action = torch.cat((action, torch.zeros(1, 9, device=env.device)), dim=1)
            obs, _ = env.step(action)
            # obs, _ = env.step(torch.randn_like(env.action_manager.action))
            count += 1

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
