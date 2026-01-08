from copy import deepcopy
import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets.articulation import ArticulationCfg


FRANKA_ARM_CFG = ArticulationCfg(
    prim_path="{ENV_REGEX_NS}/Robot",
    spawn=sim_utils.UsdFileCfg(
        usd_path="./assets/franka_arm/franka_arm.usda",
        activate_contact_sensors=True,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=True,
            retain_accelerations=True,
            max_depenetration_velocity=5.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=False,
            solver_position_iteration_count=8,
            solver_velocity_iteration_count=0,
        ),
        joint_drive_props=sim_utils.JointDrivePropertiesCfg(drive_type="force"),
        fixed_tendons_props=sim_utils.FixedTendonPropertiesCfg(
            limit_stiffness=30.0, damping=0.1
        ),
        variants={"Gripper": "None", "Mesh": "Performance"},
        # Arm link collisions are selectively disabled in env setup for performance
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.0),
        joint_pos={
            "panda_joint1": 0.0,
            "panda_joint2": -1.3672,
            "panda_joint3": 0.0,
            "panda_joint4": -1.6537,
            "panda_joint5": 0.0,
            "panda_joint6": 2.8588,
            "panda_joint7": -0.7853981633974483, # -45 degrees
        },
    ),
    actuators={
        "panda_shoulder": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[1-4]"],
            effort_limit_sim=87.0,
            stiffness=10000.0,
            damping=1000.0,
        ),
        "panda_forearm": ImplicitActuatorCfg(
            joint_names_expr=["panda_joint[5-7]"],
            effort_limit_sim=12.0,
            stiffness=10000.0,
            damping=1000.0,
        ),
    },
    soft_joint_pos_limit_factor=1.0,
)

def get_franka_hand_cfg():
    FRANKA_HAND_CFG = deepcopy(FRANKA_ARM_CFG)
    FRANKA_HAND_CFG.spawn.variants["Gripper"] = "Default"  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    FRANKA_HAND_CFG.init_state.joint_pos["panda_joint1"] = 0.0
    FRANKA_HAND_CFG.init_state.joint_pos["panda_joint2"] = 0.0
    FRANKA_HAND_CFG.init_state.joint_pos["panda_joint3"] = 0.0
    FRANKA_HAND_CFG.init_state.joint_pos["panda_joint4"] = -1.0
    FRANKA_HAND_CFG.init_state.joint_pos["panda_joint5"] = 0.0
    FRANKA_HAND_CFG.init_state.joint_pos["panda_joint6"] = 1.5707
    FRANKA_HAND_CFG.init_state.joint_pos["panda_joint7"] = -0.7853981633974483
    FRANKA_HAND_CFG.init_state.joint_pos["panda_finger_joint.*"] = 0.0  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    FRANKA_HAND_CFG.actuators["panda_finger"] = ImplicitActuatorCfg(
        joint_names_expr=["panda_finger_joint.*"],
        effort_limit_sim=20.0,
        velocity_limit_sim=100.0,
        stiffness=600.0,
        damping=10.0,
    )
    return FRANKA_HAND_CFG


def get_allegro_right_cfg():
    ALLEGRO_RIGHT_CFG = deepcopy(FRANKA_ARM_CFG)
    ALLEGRO_RIGHT_CFG.spawn.variants["Gripper"] = "AllegroHand_right"  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    ALLEGRO_RIGHT_CFG.init_state.joint_pos["joint_([0-9]|1[0-1])_0"] = 0.0 # fingers
    # thumb
    ALLEGRO_RIGHT_CFG.init_state.joint_pos["joint_12_0"] = 0.5
    ALLEGRO_RIGHT_CFG.init_state.joint_pos["joint_13_0"] = 0.2
    ALLEGRO_RIGHT_CFG.init_state.joint_pos["joint_14_0"] = 0.75
    ALLEGRO_RIGHT_CFG.init_state.joint_pos["joint_15_0"] = 0.5
    ALLEGRO_RIGHT_CFG.actuators["fingers"] = ImplicitActuatorCfg(
        joint_names_expr=["joint_.*_0"],
        effort_limit_sim=10.0,
        velocity_limit_sim=100.0,
        stiffness=400.0,
        damping=10.0,
    )
    return ALLEGRO_RIGHT_CFG


def get_orca_left_cfg():
    ORCA_LEFT_CFG = deepcopy(FRANKA_ARM_CFG)
    ORCA_LEFT_CFG.spawn.variants["Gripper"] = "OrcaHand_left"  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    ORCA_LEFT_CFG.init_state.joint_pos["left_.*"] = 0.0
    ORCA_LEFT_CFG.actuators["wrist"] = ImplicitActuatorCfg(
        joint_names_expr=["left_wrist"],
        effort_limit_sim=100.0,
        velocity_limit_sim=100.0,
        stiffness=10000.0,
        damping=1000.0,
    )
    ORCA_LEFT_CFG.actuators["thumb"] = ImplicitActuatorCfg(
        joint_names_expr=[
            "left_thumb_mcp",
            "left_thumb_abd",
            "left_thumb_pip",
            "left_thumb_dip",
        ],
        effort_limit_sim=1.0,
        velocity_limit_sim=100.0,
        stiffness=10000.0,
        damping=1000.0,
    )
    ORCA_LEFT_CFG.actuators["fingers"] = ImplicitActuatorCfg(
        joint_names_expr=["left_(index|middle|ring|pinky)_(abd|mcp|pip)"],
        effort_limit_sim=100.0,
        velocity_limit_sim=100.0,
        stiffness=10000.0,
        damping=1000.0,
    )
    return ORCA_LEFT_CFG


def get_svh_left_cfg():
    SVH_LEFT_CFG = deepcopy(FRANKA_ARM_CFG)
    SVH_LEFT_CFG.spawn.variants["Gripper"] = "SVH_left"  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    SVH_LEFT_CFG.actuators["thumb"] = ImplicitActuatorCfg(
        joint_names_expr=["Left_Hand_Thumb_Flexion", "Left_Hand_Thumb_Opposition"],
        effort_limit_sim=100.0,
        velocity_limit_sim=100.0,
        stiffness=10000.0,
        damping=1000.0,
    )
    SVH_LEFT_CFG.actuators["index"] = ImplicitActuatorCfg(
        joint_names_expr=[
            "Left_Hand_Index_Finger_Proximal",
            "Left_Hand_Index_Finger_Distal",
        ],
        effort_limit_sim=100.0,
        velocity_limit_sim=100.0,
        stiffness=10000.0,
        damping=1000.0,
    )
    SVH_LEFT_CFG.actuators["middle"] = ImplicitActuatorCfg(
        joint_names_expr=[
            "Left_Hand_Middle_Finger_Proximal",
            "Left_Hand_Middle_Finger_Distal",
        ],
        effort_limit_sim=100.0,
        velocity_limit_sim=100.0,
        stiffness=10000.0,
        damping=1000.0,
    )
    SVH_LEFT_CFG.actuators["ring"] = ImplicitActuatorCfg(
        joint_names_expr=["Left_Hand_Ring_Finger"],
        effort_limit_sim=100.0,
        velocity_limit_sim=100.0,
        stiffness=10000.0,
        damping=1000.0,
    )
    SVH_LEFT_CFG.actuators["pinky"] = ImplicitActuatorCfg(
        joint_names_expr=["Left_Hand_Pinky"],
        effort_limit_sim=100.0,
        velocity_limit_sim=100.0,
        stiffness=10000.0,
        damping=1000.0,
    )
    SVH_LEFT_CFG.actuators["spread"] = ImplicitActuatorCfg(
        joint_names_expr=["Left_Hand_Finger_Spread"],
        effort_limit_sim=100.0,
        velocity_limit_sim=100.0,
        stiffness=10000.0,
        damping=1000.0,
    )
    return SVH_LEFT_CFG


# FIXME: Broken ATM: in the physics inspector, the joints say: "Add Drive API"
def get_shadow_right_cfg():
    SHADOW_RIGHT_CFG = deepcopy(FRANKA_ARM_CFG)
    SHADOW_RIGHT_CFG.spawn.variants["Gripper"] = "ShadowHand_right"  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    SHADOW_RIGHT_CFG.init_state.joint_pos["robot0_.*"] = 0.0
    SHADOW_RIGHT_CFG.actuators["fingers"] = ImplicitActuatorCfg(
        joint_names_expr=[
            "robot0_WR.*",
            "robot0_(FF|MF|RF|LF|TH)J(3|2|1)",
            "robot0_(LF|TH)J4",
            "robot0_THJ0",
        ],
        effort_limit_sim={
            "robot0_WRJ1": 4.785,
            "robot0_WRJ0": 2.175,
            "robot0_(FF|MF|RF|LF)J1": 0.7245,
            "robot0_FFJ(3|2)": 0.9,
            "robot0_MFJ(3|2)": 0.9,
            "robot0_RFJ(3|2)": 0.9,
            "robot0_LFJ(4|3|2)": 0.9,
            "robot0_THJ4": 2.3722,
            "robot0_THJ3": 1.45,
            "robot0_THJ(2|1)": 0.99,
            "robot0_THJ0": 0.81,
        },
        stiffness={
            "robot0_WRJ.*": 5.0,
            "robot0_(FF|MF|RF|LF|TH)J(3|2|1)": 1.0,
            "robot0_(LF|TH)J4": 1.0,
            "robot0_THJ0": 1.0,
        },
        damping={
            "robot0_WRJ.*": 0.5,
            "robot0_(FF|MF|RF|LF|TH)J(3|2|1)": 0.1,
            "robot0_(LF|TH)J4": 0.1,
            "robot0_THJ0": 0.1,
        },
    )
    return SHADOW_RIGHT_CFG
