"""Environment configurations for Nine Linked Rings project.

This package contains environment definitions that can be used for:
- Teleoperation
- RL training
- Evaluation
"""

import gymnasium as gym

# Register custom environments with gymnasium
gym.register(
    id="NineRingsInspire-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": "environments.nine_rings_inspire_env_cfg:NineRingsInspireEnvCfg",
    },
)

__all__ = ["NineRingsInspire-v0"]

