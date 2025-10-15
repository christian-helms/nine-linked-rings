"""Configuration examples for Nine Rings teleoperation with Inspire hand.

This file demonstrates different retargeter configurations for various use cases.
The Inspire hand has 19 DOF (7 arm + 12 hand joints) providing full dexterous control.
"""

from teleoperation.retargeters.manus_vive_inspire_retargeter_cfg import ManusViveInspireRetargeterCfg

# ==============================================================================
# Example 1: Default Configuration
# ==============================================================================
# Balanced settings for general teleoperation

default_cfg = ManusViveInspireRetargeterCfg(
    pos_scale=1.0,        # 1:1 hand position to robot position
    rot_scale=1.0,        # 1:1 hand rotation to robot rotation
    finger_scale=1.0,     # 1:1 finger joint mapping
    smoothing=0.3,        # Moderate smoothing for natural movement
)

# ==============================================================================
# Example 2: High Sensitivity, Low Smoothing
# ==============================================================================
# For fast, responsive control. Good for quick manipulation tasks.
# Trade-off: Less smooth, may be jittery

high_response_cfg = ManusViveInspireRetargeterCfg(
    pos_scale=2.0,        # Amplify hand movements (small hand motion = large robot motion)
    rot_scale=2.0,        # Amplify rotations
    finger_scale=1.2,     # Slightly amplify finger movements
    smoothing=0.1,        # Minimal smoothing for quick response
)

# ==============================================================================
# Example 3: Low Sensitivity, High Smoothing
# ==============================================================================
# For precise, smooth control. Good for delicate tasks requiring fine control.
# Trade-off: Slower response, but very stable

smooth_cfg = ManusViveInspireRetargeterCfg(
    pos_scale=0.5,        # Reduce sensitivity (large hand motion = small robot motion)
    rot_scale=0.5,        # Reduce rotation sensitivity
    finger_scale=1.0,     # Keep 1:1 finger mapping
    smoothing=0.5,        # Heavy smoothing for very smooth movements
)

# ==============================================================================
# Example 4: Fine Manipulation
# ==============================================================================
# Optimized for precision tasks like the Nine Linked Rings puzzle

precision_cfg = ManusViveInspireRetargeterCfg(
    pos_scale=0.7,        # Reduced for fine positioning
    rot_scale=0.8,        # Slightly reduced for controlled orientation
    finger_scale=1.0,     # Full finger control needed for ring manipulation
    smoothing=0.4,        # Balanced smoothing to prevent tremors
)

# ==============================================================================
# Example 5: Recording Demonstrations
# ==============================================================================
# Optimized for recording clean, reproducible demonstrations for IL/RL

recording_cfg = ManusViveInspireRetargeterCfg(
    pos_scale=1.0,        # Standard 1:1 mapping
    rot_scale=1.0,        # Standard 1:1 mapping
    finger_scale=1.0,     # Standard 1:1 mapping
    smoothing=0.35,       # Slightly higher smoothing to remove noise
)

# ==============================================================================
# Example 6: Testing/Debugging
# ==============================================================================
# Highly damped for safe testing of new setups

safe_testing_cfg = ManusViveInspireRetargeterCfg(
    pos_scale=0.3,        # Very low sensitivity
    rot_scale=0.3,        # Very low sensitivity
    finger_scale=0.5,     # Reduced finger motion for safety
    smoothing=0.7,        # Heavy smoothing
)

# ==============================================================================
# Example 7: Expert User
# ==============================================================================
# For experienced users who want direct, unfiltered control

expert_cfg = ManusViveInspireRetargeterCfg(
    pos_scale=1.5,        # Moderate amplification
    rot_scale=1.5,        # Moderate amplification
    finger_scale=1.3,     # Amplify finger motions for full range
    smoothing=0.15,       # Minimal smoothing for direct feel
)

# ==============================================================================
# Example 8: Large Workspace
# ==============================================================================
# When you need to cover a large robot workspace with limited hand movement

large_workspace_cfg = ManusViveInspireRetargeterCfg(
    pos_scale=3.0,        # High amplification for large motions
    rot_scale=1.5,        # Moderate rotation amplification
    finger_scale=1.0,     # Keep fingers 1:1
    smoothing=0.25,       # Light smoothing to handle amplified noise
)

# ==============================================================================
# How to Use
# ==============================================================================
"""
To use these configurations in your teleoperation script:

from teleoperation.retargeters.manus_vive_inspire_retargeter_cfg import (
    ManusViveInspireRetargeter,
)
from teleoperation.config_example import precision_cfg  # Import desired config

# Create retargeter with chosen configuration
retargeter = ManusViveInspireRetargeter(precision_cfg)

# Or override specific parameters
from teleoperation.config_example import default_cfg

custom_cfg = default_cfg
custom_cfg.pos_scale = 1.5  # Modify just one parameter
retargeter = ManusViveInspireRetargeter(custom_cfg)
"""

# ==============================================================================
# Parameter Guidelines
# ==============================================================================
"""
pos_scale & rot_scale:
  - < 1.0: Reduces sensitivity (fine control)
  - = 1.0: Direct 1:1 mapping
  - > 1.0: Amplifies movements (coarse control, large workspace)

finger_scale:
  - Typically keep at 1.0 for accurate finger mapping
  - Use > 1.0 if your hand range is smaller than robot's
  - Use < 1.0 if robot fingers have limited range

smoothing:
  - 0.0: No smoothing (instant response, but jittery)
  - 0.1-0.3: Light smoothing (responsive with minor smoothing)
  - 0.3-0.5: Moderate smoothing (balanced)
  - 0.5-0.7: Heavy smoothing (very smooth but delayed)
  - > 0.7: Extreme smoothing (sluggish, use for testing only)

Trade-offs:
  - High sensitivity + Low smoothing = Fast but jittery
  - Low sensitivity + High smoothing = Smooth but slow
  - Optimal: Adjust based on task requirements
"""

# ==============================================================================
# Joint Mapping Reference
# ==============================================================================
"""
Inspire Hand (19 DOF):

Arm (7 DOF):
  - joint_1 to joint_7: Standard RM75 arm joints

Thumb (4 DOF):
  - thumb_proximal_yaw_joint: Side-to-side movement
  - thumb_proximal_pitch_joint: Up-down movement
  - thumb_intermediate_joint: Middle joint flexion
  - thumb_distal_joint: Tip joint flexion

Index Finger (2 DOF):
  - index_proximal_joint: Base joint (MCP)
  - index_intermediate_joint: Middle joint (PIP)

Middle Finger (2 DOF):
  - middle_proximal_joint: Base joint (MCP)
  - middle_intermediate_joint: Middle joint (PIP)

Ring Finger (2 DOF):
  - ring_proximal_joint: Base joint (MCP)
  - ring_intermediate_joint: Middle joint (PIP)

Pinky Finger (2 DOF):
  - pinky_proximal_joint: Base joint (MCP)
  - pinky_intermediate_joint: Middle joint (PIP)

All joints are mapped directly from Manus glove finger tracking.
"""
