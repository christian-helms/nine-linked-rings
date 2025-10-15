# Environment Registration Guide

## Two Ways to Use the Nine Rings Inspire Environment

### Method 1: Direct Instantiation (Current Implementation) ✅

This is what's currently used in `teleop_nine_rings.py`:

```python
from isaaclab.envs import ManagerBasedRLEnv
from environments.nine_rings_inspire_env_cfg import NineRingsInspireEnvCfg

# Create config
env_cfg = NineRingsInspireEnvCfg()
env_cfg.scene.num_envs = 1

# Instantiate directly
env = ManagerBasedRLEnv(cfg=env_cfg)
env.reset()
```

**Pros:**
- ✅ Simple and direct
- ✅ No registration needed
- ✅ Good for custom/experimental environments
- ✅ Works immediately

**Cons:**
- ❌ Not discoverable via `gym.registry`
- ❌ Can't use `gym.make()`

### Method 2: Gymnasium Registration (Optional)

If you want to use `gym.make()`, you need to register the environment.

#### Step 1: Register in `__init__.py`

The environment is registered in `environments/__init__.py`:

```python
import gymnasium as gym

gym.register(
    id="NineRingsInspire-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": "teleoperation.nine_rings_inspire_env_cfg:NineRingsInspireEnvCfg",
    },
)
```

#### Step 2: Import the package before using

```python
# Import to trigger registration
import environments  # This registers NineRingsInspire-v0

# Now you can use gym.make()
env = gym.make("NineRingsInspire-v0")
env.reset()
```

**Pros:**
- ✅ Standard gymnasium interface
- ✅ Discoverable via `gym.registry.all()`
- ✅ Compatible with RL frameworks expecting `gym.make()`

**Cons:**
- ❌ Requires proper package structure
- ❌ More complex for quick iterations

## Recommendation

**For teleoperation:** Use Method 1 (direct instantiation) - it's simpler and more flexible.

**For RL training:** Use Method 2 (registration) if your RL framework (like `rsl_rl`, `stable-baselines3`, etc.) expects `gym.make()`.

## Converting Between Methods

### From Direct to Registered

If you want to switch to using `gym.make()`:

```python
# Old (current)
from isaaclab.envs import ManagerBasedRLEnv
from environments.nine_rings_inspire_env_cfg import NineRingsInspireEnvCfg
env = ManagerBasedRLEnv(cfg=NineRingsInspireEnvCfg())

# New (with registration)
import environments  # Triggers registration
env = gym.make("NineRingsInspire-v0")
```

### Customizing Config with Registered Env

You can still customize the config when using `gym.make()`:

```python
import gymnasium as gym
import environments
from environments.nine_rings_inspire_env_cfg import NineRingsInspireEnvCfg

# Get custom config
custom_cfg = NineRingsInspireEnvCfg()
custom_cfg.scene.num_envs = 4
custom_cfg.sim.dt = 1.0 / 120.0  # Higher frequency

# Pass to gym.make() - NOTE: This requires modifying the registration
# For now, easier to use direct instantiation for custom configs
from isaaclab.envs import ManagerBasedRLEnv
env = ManagerBasedRLEnv(cfg=custom_cfg)
```

## Isaac Lab Environment Registration Patterns

### Standard Isaac Lab Approach

Isaac Lab's built-in environments are registered in:
`source/isaaclab_tasks/isaaclab_tasks/__init__.py`

Example:
```python
gym.register(
    id="Isaac-Lift-Cube-Franka-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": "isaaclab_tasks.manager_based.manipulation.lift:LiftEnvCfg",
    },
)
```

### Our Custom Approach

For project-specific environments, we register in the project's `__init__.py`:
```python
# teleoperation/__init__.py
gym.register(
    id="NineRingsInspire-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": "teleoperation.nine_rings_inspire_env_cfg:NineRingsInspireEnvCfg",
    },
)
```

## Troubleshooting

### "Environment NineRingsInspire-v0 not found"

**Cause:** The `environments` package wasn't imported before calling `gym.make()`.

**Solution:**
```python
import environments  # Must import to trigger registration
env = gym.make("NineRingsInspire-v0")
```

### "Module 'environments' has no attribute 'nine_rings_inspire_env_cfg'"

**Cause:** Python path doesn't include the project root.

**Solution:**
```bash
# Add to PYTHONPATH
export PYTHONPATH=/home/chris/nine-linked-rings:$PYTHONPATH

# Or use absolute imports in registration
```

### "Direct instantiation works but gym.make() fails"

**Cause:** Config entry point path is incorrect in registration.

**Check:**
```python
# Registration uses string path - must be importable
"env_cfg_entry_point": "environments.nine_rings_inspire_env_cfg:NineRingsInspireEnvCfg"

# This means Python must be able to:
from environments.nine_rings_inspire_env_cfg import NineRingsInspireEnvCfg
```

## Summary

**Current Status:**
- ✅ Environment works via direct instantiation
- ✅ Registration code provided in `environments/__init__.py`
- ✅ Both methods documented

**For Your Use Case:**
Since you're doing teleoperation (not RL training), **direct instantiation is the best choice**. It's simpler, more flexible, and doesn't require dealing with Python package paths.

If you later want to train RL policies with frameworks that expect `gym.make()`, you can switch to the registered approach.

