# Nine Linked Rings Teleoperation - Project Summary

## Overview

A streamlined teleoperation workflow for the Nine Linked Rings puzzle using ManusVive hand tracking. This package provides everything needed to control a Franka robot arm using Manus gloves and Vive trackers, with built-in demonstration recording capabilities.

## What Was Created

### Core System Files

1. **`teleop_nine_rings.py`** (Main Script)
   - Primary teleoperation application
   - Handles ManusVive device initialization
   - Manages recording sessions
   - Processes gesture commands (START, STOP, RESET)
   - Coordinates retargeting and robot control

2. **`manus_vive_retargeter_cfg.py`** (Retargeter)
   - Converts hand tracking to robot commands
   - Maps palm pose to end-effector position
   - Calculates gripper state from finger distance
   - Configurable scaling and offsets

3. **`recording_utils.py`** (Recording System)
   - `DemonstrationRecorder` class for capturing demos
   - Saves observations, actions, robot states, hand poses
   - Supports pickle, JSON, and NPZ formats
   - Automatic timestamping and metadata

4. **`nine_rings_env_cfg.py`** (Environment Config)
   - Scene configuration for the puzzle
   - Robot and puzzle USD references
   - Observation specifications
   - Environment event handling

### Utilities

5. **`demo_viewer.py`** (Analysis Tool)
   - View demonstration statistics
   - Plot position, rotation, and gripper commands
   - Export visualizations
   - Inspect recorded data structure

6. **`launch_teleop.sh`** (Launch Script)
   - Easy-to-use bash launcher
   - Prerequisite checking
   - Command-line argument handling
   - Colorized output and status messages

### Documentation

7. **`README.md`**
   - Comprehensive documentation
   - Setup instructions
   - Usage examples
   - Troubleshooting guide

8. **`QUICKSTART.md`**
   - 5-minute getting started guide
   - Step-by-step workflow
   - Common issues and solutions
   - Best practices

9. **`config_example.py`**
   - Annotated configuration template
   - Tuning parameters explained
   - Common adjustments documented
   - Copy-and-customize ready

10. **`__init__.py`**
    - Package initialization
    - Exports main classes and functions

## File Structure

```
teleoperation/
├── __init__.py                      # Package initialization
├── teleop_nine_rings.py            # Main teleoperation script ⭐
├── manus_vive_retargeter_cfg.py    # Hand-to-robot retargeting
├── recording_utils.py              # Demonstration recording
├── nine_rings_env_cfg.py           # Environment configuration
├── demo_viewer.py                  # Analysis and visualization
├── launch_teleop.sh                # Convenient launcher
├── config_example.py               # Configuration template
├── README.md                       # Full documentation
├── QUICKSTART.md                   # Quick start guide
└── SUMMARY.md                      # This file
```

## Key Features

### ✨ Streamlined Workflow
- No superfluous functionality
- Focused on Nine Linked Rings use case
- Clean separation of concerns
- Easy to understand and modify

### 🎮 Gesture Control
- **START**: Begin teleoperation and recording
- **STOP**: End session and save demonstration
- **RESET**: Reset environment to initial state

### 📹 Built-in Recording
- Automatic demonstration capture
- Multiple save formats (pickle/JSON/NPZ)
- Comprehensive metadata
- Timestamped recordings

### 🔧 Highly Configurable
- Adjustable position/rotation scaling
- Tunable gripper thresholds
- Custom XR anchor positioning
- Flexible retargeting parameters

### 📊 Analysis Tools
- Statistical summaries
- Visual plots of trajectories
- Data inspection utilities
- Export capabilities

## Quick Usage Examples

### Basic Teleoperation (No Recording)
```bash
./teleoperation/launch_teleop.sh
```

### Record Demonstrations
```bash
./teleoperation/launch_teleop.sh --record
```

### Custom Configuration
```bash
uv run teleoperation/teleop_nine_rings.py --xr \
    --record \
    --record_dir expert_demos \
    --record_format npz
```

### View Recorded Demo
```bash
uv run teleoperation/demo_viewer.py demonstrations/demo_*.pkl --plot
```

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  ManusVive Device                       │
│  (Manus Gloves + Vive Trackers + Hand Tracking)       │
└──────────────────┬──────────────────────────────────────┘
                   │ Raw hand tracking data
                   │ (joint poses, orientations)
                   ▼
┌─────────────────────────────────────────────────────────┐
│              ManusViveFrankaRetargeter                  │
│  (Converts hand poses to robot commands)               │
└──────────────────┬──────────────────────────────────────┘
                   │ Robot commands
                   │ [pos, rot, gripper]
                   ▼
┌─────────────────────────────────────────────────────────┐
│                Teleoperation Loop                       │
│  - Apply commands to robot                             │
│  - Capture state for recording                         │
│  - Handle gesture callbacks                            │
└──────────────────┬──────────────────────────────────────┘
                   │ Observations, actions
                   │ robot states, hand poses
                   ▼
┌─────────────────────────────────────────────────────────┐
│           DemonstrationRecorder                         │
│  (Saves data for imitation learning)                   │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

1. **Input**: ManusVive captures hand and wrist poses
2. **Retargeting**: Retargeter converts to robot commands
3. **Execution**: Commands applied to Franka robot
4. **Recording**: State and actions captured
5. **Storage**: Demonstrations saved to disk

## Demonstration Data Structure

Each recorded demonstration contains:
```python
{
    "observations": [array(...), ...],    # Environment observations
    "actions": [array(...), ...],        # Robot commands (7-DOF)
    "robot_states": [{...}, ...],        # Joint pos/vel/forces
    "hand_poses": [{...}, ...],          # Raw tracking data
    "timestamps": [0.0, 0.016, ...],     # Relative time (seconds)
    "metadata": {
        "start_time": "2025-01-12T14:30:22",
        "end_time": "2025-01-12T14:35:47",
        "duration_seconds": 325.0,
        "num_steps": 19500
    }
}
```

## Extending the System

### Add Custom Gestures
Edit `manus_vive.py`:
```python
device.add_callback("CUSTOM", my_custom_function)
```

### Modify Retargeting
Edit `manus_vive_retargeter_cfg.py`:
```python
def retarget(self, raw_data: dict) -> np.ndarray:
    # Add custom retargeting logic
    pass
```

### Change Recording Format
Add new format in `recording_utils.py`:
```python
elif self.format == "hdf5":
    # Implement HDF5 saving
```

### Add Observations
Edit `nine_rings_env_cfg.py`:
```python
class PolicyCfg(ObsGroup):
    custom_obs = ObsTerm(func=my_custom_observation)
```

## Integration Points

### With IsaacLab Tasks
```python
import isaaclab_tasks
env = gym.make("Isaac-NineRings-v0", cfg=env_cfg)
```

### With Imitation Learning
```python
from teleoperation.recording_utils import load_demonstration
demo = load_demonstration("demo.pkl")
# Use demo['actions'] and demo['observations'] for BC/IRL
```

### With Custom Robots
Subclass `ManusViveFrankaRetargeter`:
```python
class ManusViveUR5Retargeter(RetargeterBase):
    def retarget(self, raw_data):
        # UR5-specific retargeting
        pass
```

## Next Steps

1. **Test Hardware**: Run basic teleoperation without recording
2. **Calibrate**: Tune retargeter parameters for smooth control
3. **Record Demos**: Collect expert demonstrations
4. **Analyze Data**: Use demo_viewer to inspect recordings
5. **Train Policy**: Use demonstrations for imitation learning

## Hardware Requirements

- Manus Quantum/Prime gloves
- 2x Vive trackers (wrists)
- 2x Vive base stations
- VR-ready PC (optional: VR headset)
- Franka Emika Panda robot (or simulation)

## Software Requirements

- Isaac Sim 5.1+
- Isaac Lab
- Python 3.10+
- Manus SDK
- SteamVR

## Support and Troubleshooting

Refer to:
- `README.md` for detailed documentation
- `QUICKSTART.md` for common issues
- `config_example.py` for parameter tuning
- Isaac Lab documentation for environment setup

## License

BSD-3-Clause (consistent with Isaac Lab)

---

**Created**: January 2025  
**Purpose**: Streamlined teleoperation for Nine Linked Rings puzzle  
**Status**: Ready for testing and demonstration recording

