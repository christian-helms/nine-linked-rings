# URDF Migration Notes

## Overview
The robot configuration has been migrated from USD to URDF format for better control and modularity.

## Changes Made

### 1. Robot Configuration Updated
**File**: `environments/nine_rings_inspire_env_cfg.py`

**Before**:
```python
robot = ArticulationCfg(
    spawn=sim_utils.UsdFileCfg(
        usd_path="/home/chris/nine-linked-rings/assets/assembled.usda",
        prim_path_in_usd="/World/rm75_inspire_left",
        ...
    )
)
```

**After**:
```python
robot = ArticulationCfg(
    spawn=sim_utils.UrdfFileCfg(
        asset_path="/home/chris/nine-linked-rings/robots/rm75_inspire_left_hand.urdf",
        ...
    )
)
```

### 2. Puzzle Separated
The Nine Linked Rings puzzle is now separate from the robot:
- Robot: `/home/chris/nine-linked-rings/robots/rm75_inspire_left_hand.urdf`
- Puzzle: `/home/chris/nine-linked-rings/assets/nine-linked-rings.usda`

## Robot Specifications

### RM75 Arm (7 DOF)
- `joint_1` through `joint_7`
- Standard industrial arm joints

### Inspire Left Hand (12 DOF)

**Thumb (4 DOF)**:
- `thumb_proximal_yaw_joint`: Yaw movement (side-to-side)
- `thumb_proximal_pitch_joint`: Pitch movement (up-down)
- `thumb_intermediate_joint`: Middle joint flexion (mimic)
- `thumb_distal_joint`: Tip joint flexion (mimic)

**Index Finger (2 DOF)**:
- `index_proximal_joint`: Base joint (MCP)
- `index_intermediate_joint`: Middle joint (PIP, mimic)

**Middle Finger (2 DOF)**:
- `middle_proximal_joint`: Base joint (MCP)
- `middle_intermediate_joint`: Middle joint (PIP, mimic)

**Ring Finger (2 DOF)**:
- `ring_proximal_joint`: Base joint (MCP)
- `ring_intermediate_joint`: Middle joint (PIP, mimic)

**Pinky Finger (2 DOF)**:
- `pinky_proximal_joint`: Base joint (MCP)
- `pinky_intermediate_joint`: Middle joint (PIP, mimic)

### Total: 19 DOF (7 arm + 12 hand)

**Note**: Intermediate and distal finger joints use mimic joints, so they automatically follow the proximal joint movements.

## URDF Coordinate Frame

The URDF includes a fixed `world_joint` with the following transform:
```xml
<origin xyz="0.138497 0 0" rpy="-1.57079 1.57079 0"/>
```

This means:
- X offset: 0.138497m (forward from base)
- Roll: -90° 
- Pitch: 90°

If the robot appears in an unexpected location or orientation in the simulation, you may need to adjust the `init_state` position and rotation in the configuration.

## Testing the Configuration

### 1. Visual Inspection
Run the environment and check:
- Robot appears at correct location
- Robot orientation is correct
- All joints move as expected
- Hand is properly attached to arm

### 2. Joint Control Test
```python
# Test script to verify all joints
import numpy as np

# Create environment
env = gym.make("Isaac-NineRings-Inspire-v0")

# Set all arm joints to neutral
arm_action = np.zeros(7)
env.step(arm_action)

# Test finger control
finger_action = np.ones(12) * 0.5  # Half-closed hand
env.step(finger_action)
```

### 3. Coordinate Frame Verification
Check the following frames in the viewer:
- `world_base`: Should be at origin
- `arm_base`: Should be offset and rotated per world_joint
- `rm75_link_7`: End of arm (wrist)
- `hand_base_link`: Base of hand
- Finger tips: Should be positioned correctly relative to palm

## Troubleshooting

### Robot Not Visible
1. Check URDF mesh paths are correct:
   - Arms: `../../arms/rm75/meshes/`
   - Hands: `../../hands/inspire_hand/meshes/`
2. Ensure mesh files exist at those relative paths from URDF location

### Robot in Wrong Position
Adjust `init_state` in the config:
```python
init_state=ArticulationCfg.InitialStateCfg(
    pos=(x, y, z),  # Adjust position
    rot=(w, x, y, z),  # Adjust orientation (quaternion)
)
```

### Joints Not Moving
1. Check actuator configuration in `nine_rings_inspire_env_cfg.py`
2. Verify joint names match those in URDF
3. Check effort and velocity limits

### Collisions Issues
If self-collisions are problematic:
```python
articulation_props=sim_utils.ArticulationRootPropertiesCfg(
    enabled_self_collisions=True,  # Enable if needed
    ...
)
```

## Next Steps

1. **Test Environment**: Load and verify robot appears correctly
2. **Update Retargeter**: Ensure teleoperation retargeter uses correct joint names
3. **Calibrate Control**: Tune actuator parameters for smooth control
4. **Record Demos**: Test demonstration recording with new configuration

## References

- URDF: `/home/chris/nine-linked-rings/robots/rm75_inspire_left_hand.urdf`
- Config: `/home/chris/nine-linked-rings/environments/nine_rings_inspire_env_cfg.py`
- Assets: `/home/chris/nine-linked-rings/assets/nine-linked-rings.usda`

