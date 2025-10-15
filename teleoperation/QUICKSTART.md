# Quick Start Guide

This guide will get you up and running with Nine Linked Rings teleoperation in 5 minutes.

## Prerequisites Check

Before starting, verify you have:

- ✅ Manus SDK installed and configured
- ✅ Vive base stations powered on
- ✅ Vive trackers paired and visible in SteamVR
- ✅ Manus gloves connected and calibrated
- ✅ Isaac Sim 5.1+ installed

## Step 1: Environment Setup

```bash
# Navigate to project directory
cd /home/chris/nine-linked-rings

# Ensure Manus SDK is in library path
export LD_LIBRARY_PATH=/path/to/manus_sdk/lib:$LD_LIBRARY_PATH

# Verify Python environment
uv run python --version
```

## Step 2: Hardware Setup

1. **Put on Equipment**:
   - Put on Manus gloves
   - Attach Vive trackers to both wrists
   - Put on VR headset (optional, for visual feedback)

2. **Calibrate**:
   - Open Manus Core software
   - Calibrate hand tracking
   - Verify trackers are green in SteamVR

3. **Test Tracking**:
   ```bash
   # Run a quick tracking test (if available)
   # Check that wrist positions are stable
   ```

## Step 3: Launch Teleoperation

### Without Recording (Practice Mode)

```bash
uv run teleoperation/teleop_nine_rings.py --xr
```

### With Recording (Capture Demonstrations)

```bash
uv run teleoperation/teleop_nine_rings.py --xr --record
```

### Custom Recording Directory

```bash
uv run teleoperation/teleop_nine_rings.py --xr --record \
    --record_dir ./my_expert_demos \
    --record_format npz
```

## Step 4: Perform Teleoperation

1. **Wait for initialization** - The scene will load

2. **Use START gesture** - Begin teleoperation
   - Recordings start automatically

3. **Control the robot**:
   - Move your right hand to control the arm
   - Pinch thumb and index to close gripper
   - Spread fingers to open gripper

4. **Use STOP gesture** - End teleoperation
   - Recording saves automatically

5. **Use RESET gesture** - Reset environment (if needed)

## Step 5: Review Demonstrations

View statistics of your recording:

```bash
uv run teleoperation/demo_viewer.py demonstrations/demo_20250112_143022.pkl
```

Visualize with plots:

```bash
uv run teleoperation/demo_viewer.py demonstrations/demo_20250112_143022.pkl --plot
```

Save plots for analysis:

```bash
uv run teleoperation/demo_viewer.py demonstrations/demo_20250112_143022.pkl \
    --save-plot analysis.png
```

## Common Issues

### "Device not found"
- Check SteamVR is running
- Verify trackers are visible (green icons)
- Restart Manus Core

### "No hand tracking data"
- Recalibrate Manus gloves in Manus Core
- Check glove battery level
- Verify gloves are paired

### "Robot not responding"
- Ensure START gesture was performed
- Check teleoperation is active (console message)
- Verify retargeter configuration

### "Recording not saved"
- Check STOP gesture was performed
- Verify write permissions on recording directory
- Check disk space

## Tips for Best Results

1. **Smooth Movements**: Move slowly and deliberately
2. **Calibration**: Recalibrate hands before each session
3. **Lighting**: Ensure good lighting for tracker visibility
4. **Practice**: Do a few practice runs before recording
5. **Multiple Takes**: Record several demonstrations for robustness

## Next Steps

- **Analyze Recordings**: Use `demo_viewer.py` to review your data
- **Train Policies**: Use recordings for imitation learning
- **Tune Retargeter**: Adjust scaling factors in `manus_vive_retargeter_cfg.py`
- **Add Features**: Extend with IK, obstacle avoidance, etc.

## Emergency Stop

Press `Ctrl+C` in the terminal to immediately stop teleoperation and save any active recording.

## Support

If you encounter issues:
1. Check the main README.md for detailed documentation
2. Review error messages in the console
3. Verify hardware is properly connected
4. Check Isaac Lab and Isaac Sim versions

