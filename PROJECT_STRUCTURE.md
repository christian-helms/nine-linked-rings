# Nine Linked Rings - Project Structure

This document explains the organization of the Nine Linked Rings project.

## Directory Structure

```
nine-linked-rings/
├── environments/              # Environment configurations (shared across all workflows)
│   ├── __init__.py           # Gymnasium registration
│   └── nine_rings_inspire_env_cfg.py  # Inspire hand environment
│
├── teleoperation/            # Teleoperation workflows
│   ├── retargeters/         # Hand retargeting configurations
│   │   ├── __init__.py
│   │   └── manus_vive_inspire_retargeter_cfg.py
│   ├── teleop_nine_rings.py  # Main teleoperation script
│   ├── recording_utils.py    # Demonstration recording
│   ├── demo_viewer.py        # Visualization tool (updated for 19 DOF)
│   ├── config_example.py     # Configuration examples
│   ├── test_setup.py         # Setup testing
│   └── *.md                  # Documentation
│
├── learning/                 # RL/IL training (future)
│   └── __init__.py
│
├── evaluation/               # Policy evaluation (future)
│   └── __init__.py
│
├── scripts/                  # IsaacLab reference scripts (gradually being replaced)
│   └── environments/
│       └── teleoperation/
│
├── source/                   # IsaacLab source code
│   ├── isaaclab/
│   ├── isaaclab_tasks/
│   └── ...
│
└── assets/                   # USD assets and models
    ├── assembled.usda
    └── ...
```

## Design Philosophy

### Separation of Concerns

The project uses a **custom root-level structure** rather than following IsaacLab's `scripts/` convention for these reasons:

1. **Clear Workflow Separation:** Each major workflow (teleoperation, learning, evaluation) has its own top-level directory
2. **Shared Resources:** Environment configs in `environments/` can be used by any workflow
3. **Research-Friendly:** Easier to navigate and understand for collaborators
4. **Flexibility:** Not constrained by IsaacLab's generic structure

### Import Patterns

**Environments:**
```python
from environments.nine_rings_inspire_env_cfg import NineRingsInspireEnvCfg
```

**Retargeters:**
```python
from teleoperation.retargeters.manus_vive_inspire_retargeter_cfg import (
    ManusViveInspireRetargeter,
    ManusViveInspireRetargeterCfg,
)
```

**Utilities:**
```python
from teleoperation.recording_utils import DemonstrationRecorder
```

## Module Descriptions

### `environments/`

Contains environment configurations that define:
- Robot articulation (RM75 Inspire hand)
- Scene layout (Nine Linked Rings puzzle)
- Physics settings
- Observation/action spaces
- Reward functions (for RL)

**Purpose:** Shared across teleoperation, training, and evaluation

### `teleoperation/`

Contains teleoperation-specific code:
- **`retargeters/`**: Maps hand tracking → robot commands
- **`teleop_nine_rings.py`**: Main teleoperation loop
- **`recording_utils.py`**: Records demonstrations for IL
- **`demo_viewer.py`**: Visualizes recorded demonstrations
- **`config_example.py`**: Example retargeter configurations

**Purpose:** Human-in-the-loop data collection

### `learning/`

Future home for training scripts:
- Imitation learning (BC, DAgger, etc.)
- Reinforcement learning (PPO, SAC, etc.)
- Training configurations
- Model checkpoints

**Purpose:** Policy learning from demonstrations or interaction

### `evaluation/`

Future home for evaluation tools:
- Policy evaluation scripts
- Success rate metrics
- Benchmarking tools
- Visualization

**Purpose:** Quantitative assessment of learned policies

## Workflow Examples

### Teleoperation

```bash
# Record expert demonstrations
cd /home/chris/nine-linked-rings
uv run teleoperation/teleop_nine_rings.py --record

# View recorded demonstration
uv run teleoperation/demo_viewer.py demonstrations/demo_*.pkl --plot
```

### Future: Training (Example)

```bash
# Train BC policy from demonstrations
uv run learning/train_bc.py --demo_dir demonstrations/ --epochs 100

# Evaluate trained policy
uv run evaluation/eval_policy.py --policy_path checkpoints/bc_policy.pt
```

## Migration from `scripts/`

The `scripts/` folder contains IsaacLab's reference implementations. As we develop custom workflows:

1. ✅ Environment configs → `environments/`
2. ✅ Teleoperation → `teleoperation/`
3. 🔄 Learning scripts → `learning/` (as needed)
4. 🔄 Evaluation → `evaluation/` (as needed)

The `scripts/` folder will remain for reference and can be gradually cleaned up.

## Key Features

### Environment

- **19 DOF Control:** 7 arm + 12 hand (thumb: 4, fingers: 8)
- **Proper Physics:** Isaac Lab environment with collision detection
- **Gymnasium Registration:** Optional `gym.make()` support

### Retargeting

- **Full Hand Mapping:** Direct joint-to-joint for all 5 fingers
- **Configurable:** Sensitivity, smoothing, per-finger scaling
- **Production Ready:** Robust error handling, validation

### Recording

- **Comprehensive Data:** Actions, observations, robot state, raw hand data
- **Multiple Formats:** Pickle, JSON, NPZ
- **Metadata:** Timestamps, duration, statistics

### Visualization

- **Auto-Detection:** Handles both 19 DOF (Inspire) and 7 DOF (Franka)
- **Grouped Plots:** Arm, thumb, fingers separately
- **Statistics:** Joint ranges, duration, frequency

## Documentation

- **`teleoperation/DEXTEROUS_HAND_CONTROL.md`**: Usage guide
- **`teleoperation/IMPLEMENTATION_SUMMARY.md`**: Technical details
- **`teleoperation/ENVIRONMENT_REGISTRATION.md`**: Registration guide
- **`PROJECT_STRUCTURE.md`** (this file): Organization

## Next Steps

1. **Collect Demonstrations:** Use teleoperation to record expert data
2. **Implement Learning:** Add BC/IL algorithms in `learning/`
3. **Add Evaluation:** Create metrics and benchmarks in `evaluation/`
4. **Cleanup:** Gradually remove unused `scripts/` files

## Questions?

See the documentation in `teleoperation/` or check the inline comments in the code.

