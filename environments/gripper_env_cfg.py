# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Configuration for Nine Linked Rings environment."""

from __future__ import annotations
import time

from carb.input import KeyboardInput, acquire_input_interface

if __name__ == "__main__":
    import argparse
    import torch

    from isaaclab.app import AppLauncher

    parser = argparse.ArgumentParser(description="Tutorial on creating a cartpole base environment.")
    parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to spawn.")
    AppLauncher.add_app_launcher_args(parser)
    args_cli = parser.parse_args()
    args_cli.xr = True
    # Enable asynchronous rendering for better performance with XR
    # args_cli.kit_args = "--/omni/replicator/asyncRendering=true --/app/asyncRendering=true --/app/asyncRenderingLowLatency=true"
    app_launcher = AppLauncher(args_cli)
    simulation_app = app_launcher.app


import isaaclab.envs.mdp as mdp
import isaaclab.sim as sim_utils
from isaaclab.sim.schemas import schemas_cfg, schemas
from assets.assemblies_cfg import get_franka_hand_cfg, get_allegro_right_cfg # noqa: F401
from isaaclab.assets import AssetBaseCfg
from isaaclab.controllers import DifferentialIKControllerCfg
from isaaclab.envs import ManagerBasedEnv, ManagerBasedEnvCfg
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR
from isaaclab.sensors import ContactSensorCfg


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
            usd_path="./assets/nine_linked_rings/three_linked_rings_simplified.usd",
            scale=(0.3, 0.3, 0.3),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=(0.3, -0.2, 0.5014),  # Position in front of robot
            rot=(0.0, 0.0, 0.0, 0.0),
        ),
    )

    robot = get_franka_hand_cfg()

    contact_sensor = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot/panda_(leftfinger|rightfinger)",
        update_period=0.0,  # Update every physics step
        history_length=0,
        debug_vis=False,
    )

    ee_start = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/ee_start",
        spawn=sim_utils.UsdFileCfg(
            usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/UIElements/frame_prim.usd",
            scale=(0.001, 0.001, 0.001),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=(0.3, 0.0, 0.8),
            rot=(0.0, 0.7071, 0.7071, 0.0),
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
            ik_method="dls",
         ),
    )

    hand_action = mdp.actions.JointPositionActionCfg(
        asset_name="robot",
        joint_names=["panda_finger_joint1"],
        scale=1.0,
        use_default_offset=False,
        preserve_order=True,
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
        # Viewer settings (rotated 90 degrees around Z-axis)
        self.viewer.eye = (-0.5, -0.3, 1.4)
        self.viewer.lookat = (0.2, 0.0, 1.0)

        # Simulation settings
        self.decimation = 10
        self.sim.dt = 1.0 / 240.0
        self.sim.render_interval = 3
        self.sim.device = "cuda:0"

        # PhysX performance tuning - reduce solver iterations for speed
        # Standalone Isaac Sim uses lower defaults for interactive use
        # self.sim.physx.min_position_iteration_count = 1
        # self.sim.physx.max_position_iteration_count = 32  # Lower from 255
        # self.sim.physx.min_velocity_iteration_count = 0
        # self.sim.physx.max_velocity_iteration_count = 32  # Lower from 255

        # Episode length
        self.episode_length_s = 300.0  # 5 minutes for teleoperation


def disable_arm_link_collisions(num_envs: int):
    """Disable collisions on arm links after robot is spawned.
    
    This keeps only end effector collisions (hand + fingers) for better performance.
    """
    collision_disabled_cfg = schemas_cfg.CollisionPropertiesCfg(collision_enabled=False)
    
    # Arm links to disable collisions on (keep panda_hand, panda_leftfinger, panda_rightfinger enabled)
    arm_links = [
        # "panda_leftfinger",
        # "panda_rightfinger",
        "panda_hand",
        "panda_link0",
        "panda_link1",
        "panda_link2",
        "panda_link3",
        "panda_link4",
        "panda_link5",
        "panda_link6",
        "panda_link7",
    ]
    
    for env_idx in range(num_envs):
        for link in arm_links:
            prim_path = f"/World/envs/env_{env_idx}/Robot/{link}"
            schemas.modify_collision_properties(prim_path, collision_disabled_cfg)
    
    print(f"[INFO] Disabled collisions on arm links: {arm_links}")


def main():
    env_cfg = NineLinkedRingsEnvCfg()
    env_cfg.scene.num_envs = args_cli.num_envs
    # Use GPU physics for better performance (default is "cuda:0")
    # env_cfg.sim.device = "cpu"  # CPU physics is much slower

    env = ManagerBasedEnv(cfg=env_cfg)
    
    # Disable collisions on arm links for better performance during manipulation
    # Only end effector (panda_hand, panda_leftfinger, panda_rightfinger) will collide
    disable_arm_link_collisions(env_cfg.scene.num_envs)
    
    print("[INFO] Press 'A' to open gripper, 'D' to close gripper.")
    import omni.appwindow
    app_window = omni.appwindow.get_default_app_window()
    keyboard = app_window.get_keyboard()
    input_interface = acquire_input_interface()
    gripper_target = 0.0
    gripper_step = 0.002
    min_gripper = 0.0
    max_gripper = 0.04

    count = 0
    env.reset()
    
    # ------- Profiling --------
    sim_hz = int(1 / env_cfg.sim.dt)
    env_hz = int(sim_hz / env_cfg.decimation)
    render_hz = int(sim_hz / env_cfg.sim.render_interval)
    print(f"Desired Sim Hz: {sim_hz}")    
    print(f"Desired Env Hz: {env_hz}")
    print(f"Desired Render Hz: {render_hz}")

    last_time = time.time()
    last_count = count

    # --------------------------

    while simulation_app.is_running():
        with torch.inference_mode():
            if input_interface.get_keyboard_value(keyboard, KeyboardInput.A):
                gripper_target += gripper_step
            elif input_interface.get_keyboard_value(keyboard, KeyboardInput.D):
                gripper_target -= gripper_step
            gripper_target = max(min_gripper, min(gripper_target, max_gripper))

            ee_goal_transl, ee_goal_quat = env.scene["ee_start"].get_local_poses()
            action = torch.cat((ee_goal_transl, ee_goal_quat), dim=1)
            hand_action = torch.full((env.num_envs, 1), gripper_target, device=env.device)
            action = torch.cat((action, hand_action), dim=1)
            
            obs, _ = env.step(action)
            # obs, _ = env.step(torch.zeros((env.num_envs, 0), device=env.device))
            count += 1


            # ------- Profiling --------
            if count - last_count == env_hz:
                current_time = time.time()

                print(f"{env_hz} steps in {current_time - last_time:.3f} seconds")
                print(f"Env Hz: {env_hz / (current_time - last_time):.3f} / {env_hz} Hz")
                print(f"Sim Hz: {sim_hz / (current_time - last_time):.3f} / {sim_hz} Hz")
                print(f"Render Hz: {render_hz / (current_time - last_time):.3f} / {render_hz} Hz")

                last_time = current_time
                last_count = count
                print("--------------------------------")
            # --------------------------

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
