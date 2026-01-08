"""VR-based teleoperation script."""

import argparse
from typing import Optional
import carb
import torch
from typing import Literal

# Parse arguments BEFORE Hydra intercepts sys.argv
parser = argparse.ArgumentParser(
    description="Teleoperate Nine Linked Rings puzzle with ManusVive and Inspire hand."
)
parser.add_argument(
    "--num_envs",
    type=int,
    default=1,
    help="Number of environments (typically 1 for teleoperation).",
)
parser.add_argument(
    "--record",
    action="store_true",
    default=False,
    help="Enable recording of demonstrations.",
)
parser.add_argument(
    "--record_dir",
    type=str,
    default="demonstrations",
    help="Directory to save recorded demonstrations.",
)
parser.add_argument(
    "--record_format",
    type=str,
    default="pickle",
    choices=["pickle", "json", "npz"],
    help="Format for saving demonstrations.",
)
parser.add_argument(
    "--disable_fabric",
    action="store_true",
    default=False,
    help="Disable fabric and use USD I/O operations.",
)

# Append AppLauncher arguments (includes animation recording args)
from isaaclab.app import AppLauncher

AppLauncher.add_app_launcher_args(parser)

# Parse known args and keep remaining for Hydra
args_cli = parser.parse_args()

# Enable XR mode
args_cli.xr = False

# Launch the simulator BEFORE Hydra
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import hydra
from omegaconf import DictConfig

"""Rest of the script after launching the simulator."""

from isaaclab.envs import ManagerBasedEnv

from isaaclab.devices.haply.se3_haply import HaplyDevice
from isaaclab.sim.schemas import schemas_cfg, schemas
from teleoperation.recording_utils import DemonstrationRecorder
from isaacsim.core.prims import SingleXFormPrim
from teleoperation.retargeters.haply_retargeter import HaplyRetargeter


def _initialize_recorder(
    record: bool, record_dir: str, record_format: str
) -> Optional[DemonstrationRecorder]:
    if record:
        return DemonstrationRecorder(
            save_dir=record_dir,
            format=record_format,
        )
    return None


# State flags
is_teleoperating = False
should_reset = False
recorder = DemonstrationRecorder()


# Callback functions
def start_teleoperation() -> None:
    """Start teleoperation and recording."""
    global is_teleoperating, recorder
    is_teleoperating = True
    if recorder:
        recorder.start_recording()
    print("✓ Teleoperation started")


def stop_teleoperation() -> None:
    """Stop teleoperation and save recording."""
    global is_teleoperating, recorder
    is_teleoperating = False
    if recorder and recorder.is_recording:
        filepath = recorder.stop_recording()
        if filepath:
            print(f"✓ Demonstration saved to: {filepath}")
    print("✓ Teleoperation stopped")


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


@hydra.main(config_path="config", config_name="teleop_gripper.yaml")
def main(cfg: DictConfig) -> None:
    """Main teleoperation loop with recording capability."""

    print("Creating environment...")
    env_cfg = hydra.utils.instantiate(cfg.env)
    env_cfg.scene.robot = hydra.utils.call(cfg.robot_cfg)
    env_cfg.scene.num_envs = 1

    # Disable fabric if requested (required for Stage Recorder animation recording)

    env = ManagerBasedEnv(cfg=env_cfg)

    print("Setting up device and retargeter...")
    haply_device_cfg = hydra.utils.instantiate(cfg.haply_device_cfg)
    haply_device = HaplyDevice(haply_device_cfg)
    ee_start_pos, ee_start_quat = env.scene["ee_start"].get_local_poses()
    haply_retargeter = HaplyRetargeter(ee_start_pos.to("cpu").squeeze(0))

    print("Calibrating base position on the Haply device...")
    start_position = haply_device.advance()[:3]
    haply_retargeter.set_haply_start_position(start_position)

    print("Setting up XR anchor...")
    xr_cfg = hydra.utils.instantiate(cfg.xr_cfg)
    xr_anchor = SingleXFormPrim(
        "/XRAnchor", position=xr_cfg.anchor_pos, orientation=xr_cfg.anchor_rot
    )
    carb.settings.get_settings().set_float(
        "/persistent/xr/profile/ar/render/nearPlane", xr_cfg.near_plane
    )
    carb.settings.get_settings().set_string(
        "/persistent/xr/profile/ar/anchorMode", "custom anchor"
    )
    carb.settings.get_settings().set_string(
        "/xrstage/profile/ar/customAnchor", xr_anchor.prim_path
    )

    print("Starting simulation loop...")
    try:
        gripper_mode: Literal["open", "close"] = "open"
        gripper_target_map: dict[Literal["open", "close"], float] = {
            "open": 0.04,
            "close": 0.000,
        }
        while simulation_app.is_running():
            with torch.inference_mode():
                if should_reset:
                    env.reset()
                    continue

            command = haply_device.advance()
            command = haply_retargeter.retarget(command)
            command_position = command[:3].unsqueeze(0)
            command_orientation_quat = command[3:7].unsqueeze(0)
            buttons = command[7:]

            ee_target_pose = torch.cat(
                (command_position, command_orientation_quat), dim=1
            )

            if buttons[0]:
                gripper_mode = "open"
            elif buttons[1]:
                gripper_mode = "close"
            gripper_target = gripper_target_map[gripper_mode]
            gripper_target = torch.full((env.num_envs, 1), gripper_target)

            action = torch.cat((ee_target_pose, gripper_target), dim=1)

            obs, _ = env.step(action.to(env.device))

            # Get contact forces from both gripper fingers
            contact_sensor = env.scene["contact_sensor"]
            # Shape: (num_envs, num_bodies=2, 3) -> sum across fingers
            gripper_force = contact_sensor.data.net_forces_w.sum(dim=1)  # (num_envs, 3)
            # Push force sensed at the end-effector to the Haply device
            # haply_device.push_force(
            #     forces=gripper_force, position=torch.tensor([0], device=env.device)
            # )

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"Error during simulation: {e}")
        import traceback

        traceback.print_exc()
    finally:
        try:
            env.close()
            print("Environment closed successfully")
        except Exception as e:
            print(f"Error closing environment: {e}")

        print("\nTeleoperation session ended")


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
