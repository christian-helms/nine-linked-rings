"""Configuration for Nine Linked Rings environment with RM75+Inspire hand."""

from __future__ import annotations

if __name__ == "__main__":
    import argparse
    import torch
    from isaaclab.app import AppLauncher

    parser = argparse.ArgumentParser(
        description="Tutorial on creating a cartpole base environment."
    )
    parser.add_argument(
        "--num_envs", type=int, default=1, help="Number of environments to spawn."
    )
    AppLauncher.add_app_launcher_args(parser)
    args_cli = parser.parse_args()
    app_launcher = AppLauncher(args_cli)
    simulation_app = app_launcher.app


import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab_assets.robots.shadow_hand import SHADOW_HAND_CFG
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR
from isaaclab.envs import ManagerBasedEnvCfg, ManagerBasedEnv
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass


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
        ),
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=(0.0, 0.0, 1.0),  # Position in front of robot
        ),
    )

    # hand = SHADOW_HAND_CFG.replace(prim_path="{ENV_REGEX_NS}/Hand")

    # arm = ArticulationCfg(
    #     prim_path="{ENV_REGEX_NS}/Robot",
    #     spawn=sim_utils.UrdfFileCfg(
    #         asset_path="/home/chris/nine-linked-rings/dex-urdf/robots/assembly/rm75_inspire/rm75_inspire_left_hand.urdf",
    #         activate_contact_sensors=True,
    #         rigid_props=sim_utils.RigidBodyPropertiesCfg(
    #             disable_gravity=False,
    #             max_depenetration_velocity=5.0,
    #         ),
    #         articulation_props=sim_utils.ArticulationRootPropertiesCfg(
    #             enabled_self_collisions=False,
    #             solver_position_iteration_count=8,
    #             solver_velocity_iteration_count=0,
    #         ),
    #     ),
    #     init_state=ArticulationCfg.InitialStateCfg(
    #         # Note: URDF includes world_joint with transform: xyz="0.138497 0 0" rpy="-1.57079 1.57079 0"
    #         # Adjust pos/rot here if robot appears in wrong location/orientation
    #         pos=(0.0, 0.0, 0.0),
    #         rot=(0.7071, 0, 0, 0.7071),  # Quaternion for 90° around X (w,x,y,z)
    #         joint_pos={
    #             # Arm joints - neutral pose
    #             "joint_1": 0.0,
    #             "joint_2": 0.0,
    #             "joint_3": 0.0,
    #             "joint_4": 1.57,  # 90 degrees
    #             "joint_5": 0.0,
    #             "joint_6": 0.0,
    #             "joint_7": 0.0,
    #             # Hand joints - open hand
    #             "index_proximal_joint": 0.0,
    #             "index_intermediate_joint": 0.0,
    #             "middle_proximal_joint": 0.0,
    #             "middle_intermediate_joint": 0.0,
    #             "ring_proximal_joint": 0.0,
    #             "ring_intermediate_joint": 0.0,
    #             "pinky_proximal_joint": 0.0,
    #             "pinky_intermediate_joint": 0.0,
    #             "thumb_proximal_yaw_joint": 0.0,
    #             "thumb_proximal_pitch_joint": 0.0,
    #             "thumb_intermediate_joint": 0.0,
    #             "thumb_distal_joint": 0.0,
    #         },
    #     ),
    #     actuators={
    #         # Arm actuators
    #         "arm": ImplicitActuatorCfg(
    #             joint_names_expr=["joint_[1-7]"],
    #             effort_limit=87.0,
    #             velocity_limit=2.175,
    #             stiffness=80.0,
    #             damping=4.0,
    #         ),
    #         # Finger actuators - precise control
    #         "fingers": ImplicitActuatorCfg(
    #             joint_names_expr=[
    #                 "index_.*_joint",
    #                 "middle_.*_joint",
    #                 "ring_.*_joint",
    #                 "pinky_.*_joint",
    #             ],
    #             effort_limit=5.0,
    #             velocity_limit=3.0,
    #             stiffness=20.0,
    #             damping=1.0,
    #         ),
    #         # Thumb actuators - separate for better control
    #         "thumb": ImplicitActuatorCfg(
    #             joint_names_expr=["thumb_.*_joint"],
    #             effort_limit=5.0,
    #             velocity_limit=3.0,
    #             stiffness=20.0,
    #             damping=1.0,
    #         ),
    #     },
    # )


@configclass
class CommandsCfg:
    """Command specifications for the environment."""

    pass


@configclass
class ActionsCfg:
    """Action specifications for the environment."""

    # Full dexterous hand control
    # test_action: mdp.JointPositionActionCfg = mdp.JointPositionActionCfg(
    #     asset_name="hand",
    #     joint_names=["robot0_MFJ2"],
    #     scale=1.0,
    #     use_default_offset=True,
    # )


@configclass
class ObservationsCfg:
    """Observation specifications for the environment."""

    # @configclass
    # class PolicyCfg(ObsGroup):
    #     """Observations for policy group."""

    #     # Robot state
    #     joint_pos = ObsTerm(
    #         func=mdp.joint_pos_rel, params={"asset_cfg": SceneEntityCfg("robot")}
    #     )
    #     joint_vel = ObsTerm(
    #         func=mdp.joint_vel_rel, params={"asset_cfg": SceneEntityCfg("robot")}
    #     )

    #     # Hand pose
    #     hand_pose = ObsTerm(
    #         func=mdp.root_pos_w,
    #         params={"asset_cfg": SceneEntityCfg("robot", body_names=["rm75_link_7"])},
    #     )
    #     hand_quat = ObsTerm(
    #         func=mdp.root_quat_w,
    #         params={"asset_cfg": SceneEntityCfg("robot", body_names=["rm75_link_7"])},
    #     )

    #     def __post_init__(self):
    #         self.enable_corruption = True
    #         self.concatenate_terms = True

    # Observation groups
    # policy: PolicyCfg = PolicyCfg()


@configclass
class EventCfg:
    """Configuration for events."""

    # reset_robot_joints = EventTerm(
    #     func=mdp.reset_joints_by_scale,
    #     mode="reset",
    #     params={
    #         "position_range": (0.5, 1.5),
    #         "velocity_range": (0.0, 0.0),
    #     },
    # )


@configclass
class NineLinkedRingsEnvCfg(ManagerBasedEnvCfg):
    """Configuration for the Nine Linked Rings environment."""

    scene: NineLinkedRingsSceneCfg = NineLinkedRingsSceneCfg(
        num_envs=1, env_spacing=2.5
    )

    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    commands: CommandsCfg = CommandsCfg()
    events: EventCfg = EventCfg()

    def __post_init__(self):
        """Post initialization."""
        # Viewer settings
        self.viewer.eye = (1.0, 1.0, 1.3)
        self.viewer.lookat = (0.0, 0.0, 1.0)

        # Simulation settings
        self.decimation = 1
        self.sim.dt = 1.0 / 120.0
        self.sim.render_interval = 1
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

    count = 0
    joint_efforts = 0.5 * (torch.rand_like(env.action_manager.action) - 0.5)
    while simulation_app.is_running():
        with torch.inference_mode():
            # reset
            if count % env_cfg.episode_length_s == 0:
                count = 0
                env.reset()
                print("-" * 80)
                print("[INFO]: Resetting environment...")

            obs, _ = env.step(joint_efforts)
            count += 1

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
