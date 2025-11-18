import isaaclab.sim as sim_utils
from isaaclab.actuators.actuator_cfg import ImplicitActuatorCfg
from isaaclab.assets.articulation import ArticulationCfg

def get_orca_hand_cfg(hand_side: str):
    if hand_side not in ["left", "right"]:
        raise ValueError(f"Invalid hand side: {hand_side}")
    return ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Hand",
        spawn=sim_utils.UsdFileCfg(
            usd_path=f"assets/orca_hand/orca_hand_{hand_side}_instanceable.usd",
            activate_contact_sensors=False,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                retain_accelerations=True,
                max_depenetration_velocity=1000.0,
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=True,
                solver_position_iteration_count=8,
                solver_velocity_iteration_count=0,
                sleep_threshold=0.005,
                stabilization_threshold=0.0005,
            ),
            joint_drive_props=sim_utils.JointDrivePropertiesCfg(drive_type="force"),
            fixed_tendons_props=sim_utils.FixedTendonPropertiesCfg(limit_stiffness=30.0, damping=0.1),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.3, 1.0),
            rot=(0.0, 0.0, -0.7071, 0.7071),
            joint_pos={".*": 0.0},
        ),
        actuators={
            "wrist": ImplicitActuatorCfg(
                joint_names_expr=[f"{hand_side}_wrist"],
                effort_limit_sim=100.0,
                velocity_limit_sim=100.0,
                stiffness=5.0,
                damping=0.5,
            ),
            "thumb": ImplicitActuatorCfg(
                joint_names_expr=[
                    f"{hand_side}_thumb_mcp", 
                    f"{hand_side}_thumb_abd", 
                    f"{hand_side}_thumb_pip",
                    f"{hand_side}_thumb_dip",
                ],
                effort_limit_sim=1.0,
                velocity_limit_sim=100.0,
                stiffness=1.0,
                damping=0.1
            ),
            "fingers": ImplicitActuatorCfg(
                joint_names_expr=[f"{hand_side}_(index|middle|ring|little)_(abd|mcp|pip)"],
                effort_limit=100.0,
                velocity_limit=100.0,
                stiffness=1.0,
                damping=0.1,
            ),
        },
    )