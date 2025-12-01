"""VR-based teleoperation script."""

import argparse
import time
from typing import Optional
import hydra
from omegaconf import DictConfig

import torch

# Parse arguments
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
    "--sensitivity",
    type=float,
    default=1.0,
    help="Sensitivity multiplier for hand control.",
)
# Append AppLauncher arguments
from isaaclab.app import AppLauncher

AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# Set XR mode for ManusVive
args_cli.xr = True
args_cli.device = "cpu"

# Launch the simulator

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest of the script after launching the simulator."""

from isaaclab.envs import ManagerBasedEnv

import omni.log

from isaaclab.devices.device_base import DeviceBase
from isaaclab.devices.openxr.openxr_device import OpenXRDevice  # noqa: F401
from isaaclab.devices.openxr.xr_cfg import XrCfg  # noqa: F401
from teleoperation.recording_utils import DemonstrationRecorder


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


def reset_environment() -> None:
    """Reset the environment."""
    global should_reset
    should_reset = True
    print("✓ Environment reset triggered")


def _record_neutral_position(device: DeviceBase) -> torch.Tensor:
    print("Neutral position is going to be recorded in 5 seconds:")
    time.sleep(1)
    for i in range(4, 0, -1):
        print(f"{i}")
        time.sleep(1)
    action = device.advance()
    print("Neutral position recorded successfully")
    print("neutral_position: ", action[:7])
    time.sleep(1)
    return action[:7]


def _calibrate_device_frame(device: DeviceBase) -> None:
    """Calibrate the device."""
    print("Calibrating device frame...")

    neutral_pose = _record_neutral_position(device)

    device._retargeters[0].set_neutral_pose(neutral_pose)  # type: ignore

    print("✓ Device calibrated successfully")


def _setup_device(cfg: DictConfig, env: ManagerBasedEnv) -> DeviceBase:
    try:
        device = hydra.utils.instantiate(cfg.device)
        _calibrate_device_frame(device)
        device._retargeters[0].set_ee_start_pose(env.scene["ee_start"].get_local_poses())
        device.add_callback("START", start_teleoperation)
        device.add_callback("STOP", stop_teleoperation)
        device.add_callback("RESET", reset_environment)
        omni.log.info(str(device))
        omni.log.info("Device initialized successfully")
    except Exception as e:
        omni.log.error(f"Failed to initialize device: {e}")
        simulation_app.close()
        exit(1)

    return device


@hydra.main(config_path="config", config_name="teleop.yaml")
def main(cfg: DictConfig) -> None:
    """Main teleoperation loop with recording capability."""

    omni.log.info("Creating environment...")
    
    # Force CPU device for simulation to avoid CUDA conflicts with OpenXR
    # The environment config is loaded via hydra.utils.instantiate(cfg.env)
    # which refers to NineLinkedRingsEnvCfg. We need to override the device in the instantiated config
    # or ensure the passed config has the correct value if possible.
    # However, cfg.env is a DictConfig pointing to the class. 
    
    # Instead of modifying cfg.env directly which might be tricky if structure doesn't match,
    # we can modify the instantiated config object before creating the environment.
    
    env_cfg = hydra.utils.instantiate(cfg.env)
    # Force device to CPU
    env_cfg.sim.device = "cpu"
    env_cfg.scene.robot = hydra.utils.call(cfg.hand.assembly_cfg)
    env_cfg.actions.hand_action.joint_names = list(cfg.hand.joint_names)
    env_cfg.scene.num_envs = 1
    env = ManagerBasedEnv(cfg=env_cfg)
    omni.log.info("Environment created successfully")

    omni.log.info("Setting up device and retargeter...")
    device = _setup_device(cfg, env)
    omni.log.info("Device setup successfully")

    def reset_environment():
        omni.log.info("Resetting environment...")
        env.reset()
        device.reset()
        global should_reset
        should_reset = False

    global should_reset
    should_reset = True

    try:
        while simulation_app.is_running():
            if should_reset:
                with torch.inference_mode():
                    reset_environment()

            # Allow gradients while computing teleop commands from the device.
            with torch.inference_mode(False):
                action = device.advance()

            # Drop gradients before stepping the environment for performance reasons.
            action = action.detach()

            with torch.inference_mode():
                action = action.unsqueeze(0)  # add batch dimension
                action = action.to(env.device)

                env.step(action=action)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        omni.log.error(f"Error during simulation: {e}")
        import traceback

        traceback.print_exc()
    finally:
        try:
            env.close()
            omni.log.info("Environment closed successfully")
        except Exception as e:
            omni.log.warn(f"Error closing environment: {e}")

        print("\nTeleoperation session ended")


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
