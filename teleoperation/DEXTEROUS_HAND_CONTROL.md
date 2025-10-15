# Dexterous Hand Control for Nine Linked Rings

This document describes the full dexterous hand control implementation for teleoperation of the RM75 Inspire hand in the Nine Linked Rings puzzle environment.

## Overview

The system provides **precise 19 DOF control** of the RM75 Inspire robotic hand:
- **7 DOF arm** (RM75 robot arm joints 1-7)
- **12 DOF hand** (dexterous 5-finger control)

### Hand Joint Mapping

#### Thumb (4 DOF)
- `thumb_proximal_yaw_joint` - Side-to-side movement
- `thumb_proximal_pitch_joint` - Up-down movement  
- `thumb_intermediate_joint` - Middle joint flexion
- `thumb_distal_joint` - Tip joint flexion

#### Other Fingers (2 DOF each)
Each of the four fingers (index, middle, ring, pinky) has:
- `<finger>_proximal_joint` - Base joint flexion (MCP)
- `<finger>_intermediate_joint` - Middle joint flexion (PIP)

## Components

### 1. Environment Configuration
**File:** `environments/nine_rings_inspire_env_cfg.py`

Defines the Isaac Lab environment with:
- RM75 Inspire hand articulation with proper actuators
- Nine Linked Rings puzzle scene
- Physics settings optimized for dexterous manipulation
- Observation and action spaces for RL

### 2. Hand Retargeter
**File:** `teleoperation/retargeters/manus_vive_inspire_retargeter_cfg.py`

Maps Manus glove finger tracking to Inspire hand joints:
- Direct joint-to-joint mapping for all 12 hand DOF
- Smoothing filter for natural movement
- Configurable scaling for sensitivity
- Support for full finger flexion/extension

### 3. Teleoperation Script  
**File:** `teleop_nine_rings.py`

Main script that:
- Initializes Manus gloves + Vive trackers
- Creates Isaac Lab environment
- Retargets hand motions in real-time
- Records demonstrations for imitation learning

## Usage

### Basic Teleoperation

```bash
# Navigate to project root
cd /home/chris/nine-linked-rings

# Run with default settings
uv run teleoperation/teleop_nine_rings.py

# With recording enabled
uv run teleoperation/teleop_nine_rings.py --record --record_dir ./expert_demos

# Adjust sensitivity
uv run teleoperation/teleop_nine_rings.py --sensitivity 1.5
```

### Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--num_envs` | int | 1 | Number of parallel environments |
| `--record` | flag | False | Enable demonstration recording |
| `--record_dir` | str | "demonstrations" | Directory to save recordings |
| `--record_format` | str | "pickle" | Format: pickle, json, or npz |
| `--sensitivity` | float | 1.0 | Hand motion sensitivity multiplier |

### Gesture Controls

During teleoperation, use these gestures:
- **START** - Begin teleoperation and start recording
- **STOP** - End teleoperation and save recording  
- **RESET** - Reset environment to initial state

## Hand Tracking Data Flow

```
Manus Gloves (raw finger angles)
        ↓
Vive Trackers (6DOF hand pose)
        ↓
OpenXR Device (unified tracking data)
        ↓
ManusViveInspireRetargeter (joint mapping)
        ↓
19 DOF command array [7 arm + 12 hand]
        ↓
Isaac Lab Environment (physics simulation)
        ↓
RM75 Inspire Hand (visual + physics)
```

## Retargeting Details

### Finger Joint Extraction

The retargeter extracts the following from Manus SDK:

**Thumb:**
- CMC spread → yaw joint
- CMC flex → pitch joint
- MCP flex → intermediate joint
- IP flex → distal joint

**Other Fingers:**
- MCP flex → proximal joint
- PIP flex → intermediate joint

### Smoothing

To prevent jittery movements, exponential smoothing is applied:
```python
smoothed = alpha * previous + (1 - alpha) * current
```

Default smoothing factor: `0.3` (configurable in retargeter config)

### Joint Limits

All finger joints are clamped to safe ranges:
- **Minimum:** 0.0 radians (fully extended)
- **Maximum:** 1.47 radians (~84 degrees, fully flexed)

## Recording Format

Demonstrations are saved with the following data per timestep:

```python
{
    "observation": np.ndarray,  # Robot state observation
    "action": np.ndarray,       # 19 DOF joint commands
    "robot_state": {
        "joint_positions": np.ndarray,     # 19 DOF positions
        "joint_velocities": np.ndarray,    # 19 DOF velocities  
        "hand_pose": np.ndarray,           # 7D hand pose (pos + quat)
    },
    "hand_pose": dict,          # Raw Manus tracking data
    "timestamp": float,         # Unix timestamp
}
```

## Troubleshooting

### Environment Creation Fails

If you see `Failed to create environment`, the script will fall back to direct USD loading for visualization only. To fix:

1. **Check USD asset paths:**
   ```bash
   ls /home/chris/nine-linked-rings/assets/rm75_inspire_left_hand.usd
   ls /home/chris/nine-linked-rings/assets/assembled.usda
   ```

2. **Verify USD references:**
   The `assembled.usda` file references the Inspire hand USD. Update the path if needed:
   ```
   prepend references = @<path>/rm75_inspire_left_hand.usd@
   ```

3. **Check Isaac Lab installation:**
   ```bash
   uv run python -c "import isaaclab; print(isaaclab.__version__)"
   ```

### Hand Not Responding

1. **Check Manus SDK connection:**
   - Ensure Manus Core is running
   - Verify gloves are paired and calibrated
   - Check SteamVR shows trackers (green icons)

2. **Verify retargeter output:**
   The console will log hand commands every second when teleoperating:
   ```
   Hand command - Arm[0:7]: [...]
                 Thumb[7:11]: [...]
                 Fingers[11:19]: [...]
   ```

3. **Adjust sensitivity:**
   If movements are too small or too large:
   ```bash
   uv run teleoperation/teleop_nine_rings.py --sensitivity 0.5  # Reduce
   uv run teleoperation/teleop_nine_rings.py --sensitivity 2.0  # Increase
   ```

### Recording Issues

1. **Recordings not saving:**
   - Check write permissions on output directory
   - Ensure STOP gesture is performed to trigger save
   - Verify disk space is available

2. **Incomplete recordings:**
   - Use Ctrl+C for emergency stop (saves automatically)
   - Check console for save confirmation messages

## Next Steps

### For Research/Development

1. **Train imitation learning policies:**
   ```bash
   # Collect expert demonstrations
   uv run teleoperation/teleop_nine_rings.py --record --record_dir ./expert_demos
   
   # Train with your preferred IL algorithm (BC, DAgger, etc.)
   ```

2. **Fine-tune retargeting:**
   Edit `teleoperation/retargeters/manus_vive_inspire_retargeter_cfg.py`:
   - Adjust `finger_scale` for different ROM
   - Modify `smoothing` for responsiveness vs stability
   - Add per-finger scaling if needed

3. **Customize environment:**
   Edit `environments/nine_rings_inspire_env_cfg.py`:
   - Adjust physics parameters
   - Add cameras for vision
   - Modify observation space
   - Add reward functions for RL

### For Production Use

1. **Add IK for arm control:**
   Replace simplified arm control with proper inverse kinematics

2. **Implement force/torque feedback:**
   Use haptic feedback from Manus gloves

3. **Add collision avoidance:**
   Integrate real-time collision checking

4. **Multi-hand coordination:**
   Extend to bimanual manipulation

## Technical Specifications

### RM75 Inspire Hand

- **Total DOF:** 19 (7 arm + 12 hand)
- **Actuator Type:** Implicit (position control)
- **Update Rate:** 60 Hz
- **Effort Limits:**
  - Arm joints: 87.0 N·m
  - Hand joints: 5.0 N·m
- **Velocity Limits:**
  - Arm joints: 2.175 rad/s
  - Hand joints: 3.0 rad/s

### Manus Quantum Gloves

- **Finger Tracking:** 5 fingers, full flexion/extension
- **Update Rate:** 90 Hz
- **Accuracy:** < 5° joint angle error
- **Latency:** < 15 ms

### Vive Trackers

- **Tracking Volume:** 10m x 10m  
- **Position Accuracy:** < 2mm
- **Rotation Accuracy:** < 1°
- **Update Rate:** 90 Hz

## Citation

If you use this implementation in your research, please cite:

```bibtex
@misc{nine_linked_rings_dexterous,
  title={Dexterous Hand Teleoperation for Nine Linked Rings Puzzle},
  author={Your Name},
  year={2025},
  howpublished={\url{https://github.com/yourusername/nine-linked-rings}}
}
```

## License

See LICENSE file in the repository root.

## Support

For issues or questions:
1. Check this documentation
2. Review console error messages
3. Enable verbose logging: `export ISAAC_LOG_LEVEL=DEBUG`
4. Check Isaac Lab documentation: https://isaac-sim.github.io/IsaacLab/

