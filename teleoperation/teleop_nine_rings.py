"""Teleoperation script for the Nine Linked Rings puzzle using ManusVive 
with full dexterous hand control and absolute positioning via attached trackers."""

import argparse
from pathlib import Path
import gymnasium as gym
import numpy as np
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

# Launch the simulator

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest of the script after launching the simulator."""

from isaaclab.envs import ManagerBasedRLEnv

import omni.log
import omni.usd

from isaaclab.devices.openxr.manus_vive import ManusVive, ManusViveCfg
from isaaclab.devices.openxr.xr_cfg import XrCfg

# Import local modules
from teleoperation.retargeters.manus_vive_inspire_retargeter_cfg import (
    ManusViveInspireRetargeter,
    ManusViveInspireRetargeterCfg,
)
from teleoperation.recording_utils import DemonstrationRecorder
from environments.nine_rings_inspire_env_cfg import NineRingsInspireEnvCfg


def main() -> None:
    """Main teleoperation loop with recording capability."""

    # Initialize the recording system
    recorder = None
    if args_cli.record:
        recorder = DemonstrationRecorder(
            save_dir=args_cli.record_dir,
            format=args_cli.record_format,
        )
        omni.log.info(
            f"Recording enabled. Demonstrations will be saved to: {args_cli.record_dir}"
        )

    # State flags
    is_teleoperating = False
    should_reset = False

    # Callback functions
    def start_teleoperation() -> None:
        """Start teleoperation and recording."""
        nonlocal is_teleoperating
        is_teleoperating = True
        if recorder:
            recorder.start_recording()
        print("✓ Teleoperation started")

    def stop_teleoperation() -> None:
        """Stop teleoperation and save recording."""
        nonlocal is_teleoperating
        is_teleoperating = False
        if recorder and recorder.is_recording:
            filepath = recorder.stop_recording()
            if filepath:
                print(f"✓ Demonstration saved to: {filepath}")
        print("✓ Teleoperation stopped")

    def reset_environment() -> None:
        """Reset the environment."""
        nonlocal should_reset
        should_reset = True
        print("✓ Environment reset triggered")

    # Setup ManusVive device with Inspire hand retargeter
    try:
        retargeter_cfg = ManusViveInspireRetargeterCfg(
            pos_scale=args_cli.sensitivity,
            rot_scale=args_cli.sensitivity,
            finger_scale=1.0,
            smoothing=0.3,  # Smooth finger movements for better control
        )
        retargeter = ManusViveInspireRetargeter(retargeter_cfg)

        xr_cfg = XrCfg(
            anchor_pos=[0.0, 0.0, 0.0],
            anchor_rot=[1.0, 0.0, 0.0, 0.0],
            near_plane=0.01,
        )

        manus_vive_cfg = ManusViveCfg(xr_cfg=xr_cfg)
        device = ManusVive(manus_vive_cfg, retargeters=[retargeter])

        # Register callbacks
        device.add_callback("START", start_teleoperation)
        device.add_callback("STOP", stop_teleoperation)
        device.add_callback("RESET", reset_environment)

        omni.log.info(str(device))
        omni.log.info(
            "ManusVive device with Inspire hand retargeter initialized successfully"
        )
    except Exception as e:
        omni.log.error(f"Failed to initialize ManusVive device: {e}")
        simulation_app.close()
        return

    # Create the Isaac Lab environment with Nine Rings and Inspire hand
    try:
        omni.log.info("Creating Nine Rings Inspire Hand environment...")
        env_cfg = NineRingsInspireEnvCfg()
        env_cfg.scene.num_envs = args_cli.num_envs

        # Since this is a custom environment, we'll instantiate it directly
        # rather than using gym.make() which requires registration

        env = ManagerBasedRLEnv(cfg=env_cfg)
        omni.log.info("Environment created successfully")

        # Reset environment to initial state
        env.reset()

    except Exception as e:
        omni.log.error(f"Failed to create environment: {e}")
        omni.log.info("Note: Environment creation requires proper USD assets.")
        omni.log.info("Continuing with direct USD loading for visualization...")

        # Fallback: Load USD directly for visualization only
        from pxr import Usd, UsdGeom

        stage = omni.usd.get_context().get_stage()
        scene_path = Path("/home/chris/nine-linked-rings/assets/assembled.usda")

        if scene_path.exists():
            omni.log.info(f"Loading scene from: {scene_path}")
            # Load as reference
            stage.GetRootLayer().subLayerPaths.append(str(scene_path))
        else:
            omni.log.warn(f"Scene file not found: {scene_path}")

        env = None  # No environment, direct control only

    print("\n" + "=" * 60)
    print("NINE LINKED RINGS - DEXTEROUS HAND TELEOPERATION")
    print("=" * 60)
    print("\nGesture Controls:")
    print("  - Gesture 'START': Begin teleoperation and recording")
    print("  - Gesture 'STOP':  End teleoperation and save recording")
    print("  - Gesture 'RESET': Reset the environment")
    print("\nTeleoperation:")
    print("  - Right hand controls the RM75 Inspire dexterous hand")
    print("  - All 5 fingers are independently controlled (12 DOF)")
    print("  - Arm follows hand position and orientation (7 DOF)")
    print("  - Total: 19 DOF precise control")
    print("\nHand Mapping:")
    print("  - Thumb: 4 joints (yaw, pitch, intermediate, distal)")
    print("  - Each finger (index, middle, ring, pinky): 2 joints")
    print(f"\nSensitivity: {args_cli.sensitivity:.2f}x")
    print("=" * 60 + "\n")

    # Reset tracking
    device.reset()


    # Main simulation loop
    step_count = 0
    try:
        while simulation_app.is_running():
            simulation_app.update() # ensures that device.advance() does not hang

            # Get device command (19 DOF: 7 arm + 12 hand)
            command = device.advance()

            if is_teleoperating and command is not None:
                # Process the command
                # command shape: [7 arm joints + 12 hand joints = 19 total]

                if env is not None:
                    # Apply command to environment
                    try:
                        # Ensure command is a torch tensor on CPU (env expects batch x action_dim)
                        if isinstance(command, torch.Tensor):
                            actions = command.unsqueeze(0).float()
                        else:
                            actions = torch.from_numpy(command).unsqueeze(0).float()

                        # Step the environment
                        obs, reward, terminated, truncated, info = env.step(actions)

                        # Get robot state from environment
                        if recorder and recorder.is_recording:
                            robot_state = {
                                "joint_positions": obs["policy"]["joint_pos"][0]
                                .cpu()
                                .numpy(),
                                "joint_velocities": obs["policy"]["joint_vel"][0]
                                .cpu()
                                .numpy(),
                                "hand_pose": obs["policy"]["hand_pose"][0]
                                .cpu()
                                .numpy(),
                            }

                            # Get raw hand data
                            raw_data = device._get_raw_data()

                            # Add to recording
                            recorder.add_step(
                                observation=obs["policy"].cpu().numpy().flatten(),
                                action=command,
                                robot_state=robot_state,
                                hand_pose=raw_data,
                            )
                    except Exception as e:
                        if step_count % 300 == 0:  # Log errors occasionally
                            omni.log.warn(f"Environment step error: {e}")
                else:
                    # No environment - just log commands for debugging
                    if step_count % 60 == 0:  # Log every second at 60Hz
                        cmd_np = command.cpu().numpy() if isinstance(command, torch.Tensor) else command
                        print(f"Hand command - Arm[0:7]: {cmd_np[:7]}")
                        print(f"              Thumb[7:11]: {cmd_np[7:11]}")
                        print(f"              Fingers[11:19]: {cmd_np[11:19]}")

                    # Record even without environment
                    if recorder and recorder.is_recording:
                        cmd_np = command.cpu().numpy() if isinstance(command, torch.Tensor) else command
                        robot_state = {
                            "joint_positions": cmd_np,
                            "joint_velocities": np.zeros_like(cmd_np),
                            "hand_pose": np.zeros(7),
                        }
                        raw_data = device._get_raw_data()

                        recorder.add_step(
                            observation=np.zeros(50),  # Placeholder
                            action=command,
                            robot_state=robot_state,
                            hand_pose=raw_data,
                        )

            # Handle reset
            if should_reset:
                if env is not None:
                    env.reset()
                device.reset()
                should_reset = False
                print("Environment reset complete")

            step_count += 1

            # Display recording stats periodically
            if recorder and step_count % 300 == 0:  # Every 5 seconds
                stats = recorder.get_stats()
                if stats.get("recording", False):
                    print(
                        f"Recording: {stats['num_steps']} steps, {stats['duration_seconds']:.1f}s"
                    )

            # Display teleoperation status
            if step_count % 600 == 0 and is_teleoperating:  # Every 10 seconds
                joint_names = retargeter.get_joint_names()
                print(f"✓ Teleoperating - {len(joint_names)} DOF active")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        omni.log.error(f"Error during simulation: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Save any active recording
        if recorder and recorder.is_recording:
            filepath = recorder.stop_recording()
            if filepath:
                print(f"Final demonstration saved to: {filepath}")

        # Close environment if it was created
        if env is not None:
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
