# Nine Linked Rings Teleoperation

Streamlined teleoperation workflow for the Nine Linked Rings puzzle using ManusVive hand tracking and Vive trackers.

## Overview

This package provides a focused teleoperation setup for controlling a robotic **left** hand attached to a robotic arm to manipulate the Nine Linked Rings puzzle. 
It uses:

- **ManusVive Device**: Left Manus glove + Vive tracker for hand and wrist tracking
- **Retargeter**: Converts hand tracking data to robot commands
- **Recording System**: Saves demonstrations for imitation learning

## Setup

### Hardware Prerequisitess

1. Manus Gloves, e.g., Metagloves Pro. Only the left one is really needed.

2. One HTC Vive tracker 3.0 and at least 1 x SteamVR Base Station, preferably two of them (configured at different channels).

3. Windows machine on the same private network which runs a remote Manus Core instance to allow for easy calibration in the Manus Core GUI. The Manus-Vive-IsaacLab-Bridge connects to this remote instance.


### Manus-Vive-IsaacLab-Bridge
As of writing this the binaries of IsaacSim 5.1 were not generally available which made a custom Manus-Vive-IsaacLab-Bridge necessary: Build it by executing
sst
   ```bash
    cd manus-vive-isaaclab-bridge && make all
   ```
   (The python device code knows where to find the built .so file, i.e., no further installation needed.)

### Session Setup

1. Launch SteamVR on the Windows machine, turn on the tracker and ensure it is visible. If you are not using a headless 
2. Start Manus Core, put on the left Manus glove attached with tracker, ensure both visible and calibrate them if needed.
3. Assign the tracker to the glove if not already done so.

## Usage

### Teleoperation w/o Recording

Run the teleoperation script without recording:

```bash
uv run teleoperation/teleop_nine_rings.py --xr
```

### Teleoperation with Recording

Enable demonstration recording:

```bash
uv run teleoperation/teleop_nine_rings.py --xr --record --record_dir ./my_demos
```

### Command-Line Options

- `--record`: Enable recording of demonstrations
- `--record_dir <path>`: Directory to save demonstrations (default: `demonstrations`)
- `--record_format <format>`: Save format - `pickle`, `json`, or `npz` (default: `pickle`)
- `--num_envs <n>`: Number of environments (should be 1 for teleoperation)

## Gesture Controls

During teleoperation, use these gestures:

- **START**: Begin teleoperation and start recording
- **STOP**: End teleoperation and save recording
- **RESET**: Reset the environment to initial state

## Files

### Core Modules

- **`teleop_nine_rings.py`**: Main teleoperation script
- **`manus_vive_retargeter_cfg.py`**: Retargeter for ManusVive → Franka
- **`recording_utils.py`**: Demonstration recording and loading utilities
- **`nine_rings_env_cfg.py`**: Environment configuration for the scene

### Configuration

The retargeter can be configured by modifying `ManusViveFrankaRetargeterCfg`:

```python
@configclass
class ManusViveFrankaRetargeterCfg(RetargeterBaseCfg):
    pos_scale: float = 1.0          # Position scaling factor
    rot_scale: float = 1.0          # Rotation scaling factor
    wrist_offset: tuple = (0, 0, 0.1)  # Wrist to end-effector offset
```

## Recording Format

Demonstrations are saved with the following structure:

```python
{
    "observations": [...],      # Environment observations
    "actions": [...],          # Robot actions
    "robot_states": [...],     # Joint positions, velocities
    "hand_poses": [...],       # Hand tracking data
    "timestamps": [...],       # Relative timestamps
    "metadata": {
        "start_time": "...",
        "end_time": "...",
        "duration_seconds": ...,
        "num_steps": ...
    }
}
```

### Loading Demonstrations

Load saved demonstrations for analysis or training:

```python
from teleoperation.recording_utils import load_demonstration

demo = load_demonstration("demonstrations/demo_20250112_143022.pkl")
print(f"Demonstration has {len(demo['actions'])} steps")
```

## Gripper Control

The gripper is controlled by thumb-to-index finger distance:

- **Close**: Pinch thumb and index finger together
- **Open**: Spread thumb and index finger apart

Thresholds can be adjusted in `ManusViveFrankaRetargeter._calculate_gripper_state()`.

## Troubleshooting

### Device not connecting

1. Check Manus Core is running
2. Verify Vive trackers are visible in SteamVR
3. Check `LD_LIBRARY_PATH` includes Manus SDK

### Recording not saving

1. Ensure `--record` flag is set
2. Check write permissions for `--record_dir`
3. Verify recording was stopped with STOP gesture

### Robot not responding

1. Check retargeter configuration
2. Verify hand tracking data with `device.advance()`
3. Ensure teleoperation is active (START gesture)

## Next Steps

1. **Tune Retargeter**: Adjust scaling factors for better control
2. **Add IK Controller**: Implement inverse kinematics for smoother motion
3. **Train Policy**: Use recorded demonstrations for imitation learning
4. **Multi-hand Control**: Enable bimanual manipulation

## References

- [Isaac Lab Documentation](https://isaac-sim.github.io/IsaacLab/)
- [Manus SDK Documentation](https://docs.manus-meta.com/)
- [OpenXR Specification](https://www.khronos.org/openxr/)


