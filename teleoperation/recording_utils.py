"""Utilities for recording teleoperation demonstrations."""

from __future__ import annotations

import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


class DemonstrationRecorder:
    """Records teleoperation demonstrations for later use in imitation learning."""

    def __init__(self, save_dir: str = "demonstrations", format: str = "pickle"):
        """Initialize the demonstration recorder.

        Args:
            save_dir: Directory to save demonstrations.
            format: Save format - 'pickle', 'json', or 'npz'.
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.format = format

        # Current recording state
        self.is_recording = False
        self.current_demo = {
            "observations": [],
            "actions": [],
            "robot_states": [],
            "hand_poses": [],
            "timestamps": [],
        }
        self.start_time = None

    def start_recording(self) -> None:
        """Start a new demonstration recording."""
        self.is_recording = True
        self.start_time = datetime.now()
        self.current_demo = {
            "observations": [],
            "actions": [],
            "robot_states": [],
            "hand_poses": [],
            "timestamps": [],
        }
        print(f"[Recording] Started at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def stop_recording(self) -> str | None:
        """Stop the current recording and save to disk.

        Returns:
            str: Path to saved demonstration file, or None if not recording.
        """
        if not self.is_recording:
            print("[Recording] No active recording to stop.")
            return None

        self.is_recording = False
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # Add metadata
        self.current_demo["metadata"] = {
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "num_steps": len(self.current_demo["actions"]),
        }

        # Generate filename
        timestamp_str = self.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"demo_{timestamp_str}"

        # Save based on format
        if self.format == "pickle":
            filepath = self.save_dir / f"{filename}.pkl"
            with open(filepath, "wb") as f:
                pickle.dump(self.current_demo, f)
        elif self.format == "npz":
            filepath = self.save_dir / f"{filename}.npz"
            # Convert lists to numpy arrays
            np.savez_compressed(
                filepath,
                observations=np.array(self.current_demo["observations"]),
                actions=np.array(self.current_demo["actions"]),
                robot_states=np.array(self.current_demo["robot_states"]),
                hand_poses=np.array(self.current_demo["hand_poses"]),
                timestamps=np.array(self.current_demo["timestamps"]),
                metadata=json.dumps(self.current_demo["metadata"]),
            )
        elif self.format == "json":
            filepath = self.save_dir / f"{filename}.json"
            # Convert numpy arrays to lists for JSON serialization
            demo_serializable = self._make_serializable(self.current_demo)
            with open(filepath, "w") as f:
                json.dump(demo_serializable, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {self.format}")

        print(f"[Recording] Saved demonstration to {filepath}")
        print(f"[Recording] Duration: {duration:.2f}s, Steps: {self.current_demo['metadata']['num_steps']}")

        return str(filepath)

    def add_step(
        self,
        observation: np.ndarray,
        action: np.ndarray,
        robot_state: dict[str, Any],
        hand_pose: dict[str, np.ndarray],
    ) -> None:
        """Add a single step to the current demonstration.

        Args:
            observation: Observation array from the environment.
            action: Action array sent to the robot.
            robot_state: Dictionary containing robot joint positions, velocities, etc.
            hand_pose: Dictionary containing hand tracking data.
        """
        # TODO: pass actual simulation time step instead of querying the current time
        if not self.is_recording:
            return

        # Calculate relative timestamp
        timestamp = (datetime.now() - self.start_time).total_seconds()

        self.current_demo["observations"].append(observation.copy())
        self.current_demo["actions"].append(action.copy())
        self.current_demo["robot_states"].append(robot_state.copy())
        self.current_demo["hand_poses"].append(hand_pose.copy())
        self.current_demo["timestamps"].append(timestamp)

    def _make_serializable(self, obj: Any) -> Any:
        """Convert numpy arrays and other non-serializable objects to JSON-compatible types.

        Args:
            obj: Object to convert.

        Returns:
            JSON-serializable object.
        """
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        else:
            return obj

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the current recording session.

        Returns:
            Dictionary with recording statistics.
        """
        if not self.is_recording:
            return {"recording": False}

        duration = (datetime.now() - self.start_time).total_seconds()
        return {
            "recording": True,
            "duration_seconds": duration,
            "num_steps": len(self.current_demo["actions"]),
            "start_time": self.start_time.isoformat(),
        }


def load_demonstration(filepath: str) -> dict[str, Any]:
    """Load a saved demonstration from disk.

    Args:
        filepath: Path to the demonstration file.

    Returns:
        Dictionary containing the demonstration data.
    """
    filepath = Path(filepath)

    if filepath.suffix == ".pkl":
        with open(filepath, "rb") as f:
            return pickle.load(f)
    elif filepath.suffix == ".npz":
        data = np.load(filepath, allow_pickle=True)
        return {
            "observations": data["observations"],
            "actions": data["actions"],
            "robot_states": data["robot_states"],
            "hand_poses": data["hand_poses"],
            "timestamps": data["timestamps"],
            "metadata": json.loads(str(data["metadata"])),
        }
    elif filepath.suffix == ".json":
        with open(filepath, "r") as f:
            return json.load(f)
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")


