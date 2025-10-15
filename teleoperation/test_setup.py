#!/usr/bin/env python3
# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Test script to verify teleoperation setup without full hardware."""

import sys
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    errors = []
    
    try:
        import numpy as np
        print("  ✓ numpy")
    except ImportError as e:
        errors.append(f"numpy: {e}")
        print("  ✗ numpy")
    
    try:
        import torch
        print("  ✓ torch")
    except ImportError as e:
        errors.append(f"torch: {e}")
        print("  ✗ torch")
    
    try:
        from isaaclab.devices.device_base import DeviceBase
        print("  ✓ isaaclab.devices")
    except ImportError as e:
        errors.append(f"isaaclab.devices: {e}")
        print("  ✗ isaaclab.devices")
    
    try:
        from isaaclab.devices.openxr.manus_vive import ManusVive, ManusViveCfg
        print("  ✓ ManusVive device")
    except ImportError as e:
        errors.append(f"ManusVive: {e}")
        print("  ✗ ManusVive device")
    
    return errors


def test_local_modules():
    """Test if local teleoperation modules are valid."""
    print("\nTesting local modules...")
    errors = []
    
    try:
        from manus_vive_retargeter_cfg import ManusViveFrankaRetargeter, ManusViveFrankaRetargeterCfg
        print("  ✓ manus_vive_retargeter_cfg")
        
        # Test instantiation
        cfg = ManusViveFrankaRetargeterCfg()
        retargeter = ManusViveFrankaRetargeter(cfg)
        print("  ✓ Retargeter instantiation")
        
    except Exception as e:
        errors.append(f"retargeter_cfg: {e}")
        print(f"  ✗ manus_vive_retargeter_cfg: {e}")
    
    try:
        from recording_utils import DemonstrationRecorder, load_demonstration
        print("  ✓ recording_utils")
        
        # Test recorder instantiation
        recorder = DemonstrationRecorder(save_dir="test_demos")
        print("  ✓ DemonstrationRecorder instantiation")
        
    except Exception as e:
        errors.append(f"recording_utils: {e}")
        print(f"  ✗ recording_utils: {e}")
    
    try:
        from nine_rings_env_cfg import NineRingsTeleopEnvCfg
        print("  ✓ nine_rings_env_cfg")
    except Exception as e:
        errors.append(f"nine_rings_env_cfg: {e}")
        print(f"  ✗ nine_rings_env_cfg: {e}")
    
    return errors


def test_files():
    """Test if required files exist."""
    print("\nTesting file structure...")
    errors = []
    
    required_files = [
        "teleop_nine_rings.py",
        "manus_vive_retargeter_cfg.py",
        "recording_utils.py",
        "nine_rings_env_cfg.py",
        "demo_viewer.py",
        "launch_teleop.sh",
        "README.md",
        "QUICKSTART.md",
    ]
    
    for filename in required_files:
        filepath = Path(__file__).parent / filename
        if filepath.exists():
            print(f"  ✓ {filename}")
        else:
            errors.append(f"Missing file: {filename}")
            print(f"  ✗ {filename}")
    
    return errors


def test_scene_file():
    """Test if the scene file exists."""
    print("\nTesting scene file...")
    
    scene_path = Path("/home/chris/nine-linked-rings/assets/assembled.usda")
    if scene_path.exists():
        print(f"  ✓ Scene file found: {scene_path}")
        print(f"    Size: {scene_path.stat().st_size / 1024:.1f} KB")
        return []
    else:
        print(f"  ✗ Scene file not found: {scene_path}")
        return [f"Scene file missing: {scene_path}"]


def test_recording():
    """Test recording functionality."""
    print("\nTesting recording system...")
    errors = []
    
    try:
        from recording_utils import DemonstrationRecorder
        import numpy as np
        import tempfile
        import shutil
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Test recorder
            recorder = DemonstrationRecorder(save_dir=temp_dir, format="pickle")
            recorder.start_recording()
            
            # Add some dummy data
            for i in range(10):
                recorder.add_step(
                    observation=np.random.rand(14),
                    action=np.random.rand(7),
                    robot_state={"joint_pos": np.random.rand(7)},
                    hand_pose={"palm": np.random.rand(7)},
                )
            
            filepath = recorder.stop_recording()
            
            if filepath and Path(filepath).exists():
                print(f"  ✓ Recording created: {Path(filepath).name}")
                
                # Test loading
                from recording_utils import load_demonstration
                demo = load_demonstration(filepath)
                
                if len(demo["actions"]) == 10:
                    print("  ✓ Recording loaded correctly")
                else:
                    errors.append("Recording data mismatch")
                    print("  ✗ Recording data mismatch")
            else:
                errors.append("Recording not saved")
                print("  ✗ Recording not saved")
                
        finally:
            # Cleanup
            shutil.rmtree(temp_dir)
            
    except Exception as e:
        errors.append(f"Recording test failed: {e}")
        print(f"  ✗ Recording test failed: {e}")
    
    return errors


def main():
    """Run all tests."""
    print("=" * 60)
    print("Nine Linked Rings Teleoperation Setup Test")
    print("=" * 60)
    print()
    
    all_errors = []
    
    # Run tests
    all_errors.extend(test_files())
    all_errors.extend(test_imports())
    all_errors.extend(test_local_modules())
    all_errors.extend(test_scene_file())
    all_errors.extend(test_recording())
    
    # Summary
    print("\n" + "=" * 60)
    if all_errors:
        print(f"FAILED: {len(all_errors)} error(s) found")
        print("=" * 60)
        print("\nErrors:")
        for i, error in enumerate(all_errors, 1):
            print(f"  {i}. {error}")
        print()
        return 1
    else:
        print("SUCCESS: All tests passed!")
        print("=" * 60)
        print("\nYour teleoperation setup is ready.")
        print("Next steps:")
        print("  1. Ensure ManusVive hardware is connected")
        print("  2. Run: ./teleoperation/launch_teleop.sh")
        print("  3. See QUICKSTART.md for detailed instructions")
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())

