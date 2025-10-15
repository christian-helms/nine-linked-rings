#!/usr/bin/env python3
# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Utility script to view and analyze recorded demonstrations.

Updated to support both:
- Legacy Franka format: 7 DOF (6 pose + 1 gripper)
- Inspire hand format: 19 DOF (7 arm + 12 hand)
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from teleoperation.recording_utils import load_demonstration


def plot_demonstration(demo: dict, save_path: str | None = None) -> None:
    """Plot visualization of a demonstration.

    Args:
        demo: Loaded demonstration dictionary.
        save_path: Optional path to save the plot.
    """
    timestamps = demo["timestamps"]
    actions = np.array(demo["actions"])
    action_dim = actions.shape[-1]

    # Detect action format
    if action_dim == 19:
        # Inspire hand: 7 arm + 12 hand
        plot_inspire_hand(timestamps, actions, save_path)
    elif action_dim == 7:
        # Legacy Franka: 6 pose + 1 gripper
        plot_franka_gripper(timestamps, actions, save_path)
    else:
        print(f"Warning: Unknown action dimension {action_dim}. Plotting all dimensions.")
        plot_generic_actions(timestamps, actions, save_path)


def plot_inspire_hand(timestamps: np.ndarray, actions: np.ndarray, save_path: str | None = None) -> None:
    """Plot Inspire hand demonstration (19 DOF).

    Args:
        timestamps: Time array.
        actions: Action array [N, 19].
        save_path: Optional path to save plot.
    """
    fig, axes = plt.subplots(4, 1, figsize=(14, 12))

    # Arm joints (0:7)
    axes[0].set_title("Arm Joints (7 DOF)")
    for i in range(7):
        axes[0].plot(timestamps, actions[:, i], label=f"Joint {i+1}", linewidth=1.5)
    axes[0].set_ylabel("Joint Position (rad)")
    axes[0].legend(ncol=7, fontsize=8)
    axes[0].grid(True, alpha=0.3)

    # Thumb joints (7:11)
    axes[1].set_title("Thumb (4 DOF: Yaw, Pitch, Intermediate, Distal)")
    thumb_labels = ["Yaw", "Pitch", "Intermediate", "Distal"]
    for i, label in enumerate(thumb_labels):
        axes[1].plot(timestamps, actions[:, 7+i], label=label, linewidth=2)
    axes[1].set_ylabel("Joint Position (rad)")
    axes[1].legend(ncol=4)
    axes[1].grid(True, alpha=0.3)

    # Index and Middle fingers (11:15)
    axes[2].set_title("Index & Middle Fingers (2 DOF each: Proximal, Intermediate)")
    finger_labels = ["Index Prox", "Index Inter", "Middle Prox", "Middle Inter"]
    colors = ["#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78"]
    for i, (label, color) in enumerate(zip(finger_labels, colors)):
        axes[2].plot(timestamps, actions[:, 11+i], label=label, linewidth=2, color=color)
    axes[2].set_ylabel("Joint Position (rad)")
    axes[2].legend(ncol=4)
    axes[2].grid(True, alpha=0.3)

    # Ring and Pinky fingers (15:19)
    axes[3].set_title("Ring & Pinky Fingers (2 DOF each: Proximal, Intermediate)")
    finger_labels = ["Ring Prox", "Ring Inter", "Pinky Prox", "Pinky Inter"]
    colors = ["#2ca02c", "#98df8a", "#d62728", "#ff9896"]
    for i, (label, color) in enumerate(zip(finger_labels, colors)):
        axes[3].plot(timestamps, actions[:, 15+i], label=label, linewidth=2, color=color)
    axes[3].set_ylabel("Joint Position (rad)")
    axes[3].set_xlabel("Time (s)")
    axes[3].legend(ncol=4)
    axes[3].grid(True, alpha=0.3)

    plt.suptitle("Inspire Hand Demonstration (19 DOF)", fontsize=14, fontweight="bold")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Plot saved to: {save_path}")

    plt.show()


def plot_franka_gripper(timestamps: np.ndarray, actions: np.ndarray, save_path: str | None = None) -> None:
    """Plot Franka gripper demonstration (7 DOF).

    Args:
        timestamps: Time array.
        actions: Action array [N, 7].
        save_path: Optional path to save plot.
    """
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    # Plot position commands
    axes[0].set_title("Position Commands")
    axes[0].plot(timestamps, actions[:, 0], label="X", linewidth=2)
    axes[0].plot(timestamps, actions[:, 1], label="Y", linewidth=2)
    axes[0].plot(timestamps, actions[:, 2], label="Z", linewidth=2)
    axes[0].set_ylabel("Position (m)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Plot rotation commands
    axes[1].set_title("Rotation Commands")
    axes[1].plot(timestamps, actions[:, 3], label="Roll", linewidth=2)
    axes[1].plot(timestamps, actions[:, 4], label="Pitch", linewidth=2)
    axes[1].plot(timestamps, actions[:, 5], label="Yaw", linewidth=2)
    axes[1].set_ylabel("Rotation (rad)")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Plot gripper commands
    axes[2].set_title("Gripper Commands")
    axes[2].plot(timestamps, actions[:, 6], label="Gripper", linewidth=2, color="purple")
    axes[2].set_ylabel("Gripper State (0=closed, 1=open)")
    axes[2].set_xlabel("Time (s)")
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.suptitle("Franka Gripper Demonstration (7 DOF)", fontsize=14, fontweight="bold")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Plot saved to: {save_path}")

    plt.show()


def plot_generic_actions(timestamps: np.ndarray, actions: np.ndarray, save_path: str | None = None) -> None:
    """Plot generic actions (any dimension).

    Args:
        timestamps: Time array.
        actions: Action array [N, D].
        save_path: Optional path to save plot.
    """
    action_dim = actions.shape[-1]
    fig, ax = plt.subplots(1, 1, figsize=(14, 6))

    for i in range(action_dim):
        ax.plot(timestamps, actions[:, i], label=f"Action {i}", linewidth=1.5, alpha=0.7)

    ax.set_title(f"Action Trajectories ({action_dim} DOF)")
    ax.set_ylabel("Action Value")
    ax.set_xlabel("Time (s)")
    ax.legend(ncol=min(10, action_dim), fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Plot saved to: {save_path}")

    plt.show()


def print_demo_stats(demo: dict) -> None:
    """Print statistics about a demonstration.

    Args:
        demo: Loaded demonstration dictionary.
    """
    metadata = demo["metadata"]

    print("\n" + "=" * 60)
    print("DEMONSTRATION STATISTICS")
    print("=" * 60)
    print(f"\nRecording Info:")
    print(f"  Start Time:     {metadata['start_time']}")
    print(f"  End Time:       {metadata['end_time']}")
    print(f"  Duration:       {metadata['duration_seconds']:.2f} seconds")
    print(f"  Total Steps:    {metadata['num_steps']}")
    print(f"  Average Rate:   {metadata['num_steps'] / metadata['duration_seconds']:.1f} Hz")

    actions = np.array(demo["actions"])
    action_dim = actions.shape[-1]

    print(f"\nAction Format:")
    if action_dim == 19:
        print(f"  Type: Inspire Hand (19 DOF)")
        print(f"    - Arm: 7 DOF")
        print(f"    - Thumb: 4 DOF")
        print(f"    - Fingers: 8 DOF (4 fingers × 2)")
        
        print(f"\n  Arm Joint Range:")
        for i in range(7):
            print(f"    Joint {i+1}: [{actions[:, i].min():.3f}, {actions[:, i].max():.3f}]")
        
        print(f"\n  Thumb Joint Range:")
        thumb_names = ["Yaw", "Pitch", "Intermediate", "Distal"]
        for i, name in enumerate(thumb_names):
            print(f"    {name}: [{actions[:, 7+i].min():.3f}, {actions[:, 7+i].max():.3f}]")
        
        print(f"\n  Finger Joint Range:")
        finger_names = ["Index Prox", "Index Inter", "Middle Prox", "Middle Inter",
                       "Ring Prox", "Ring Inter", "Pinky Prox", "Pinky Inter"]
        for i, name in enumerate(finger_names):
            print(f"    {name}: [{actions[:, 11+i].min():.3f}, {actions[:, 11+i].max():.3f}]")
    
    elif action_dim == 7:
        print(f"  Type: Franka Gripper (7 DOF)")
        print(f"    - Position: 3 DOF")
        print(f"    - Rotation: 3 DOF")
        print(f"    - Gripper: 1 DOF")
        
        print(f"\n  Position Range:")
        print(f"    X: [{actions[:, 0].min():.3f}, {actions[:, 0].max():.3f}]")
        print(f"    Y: [{actions[:, 1].min():.3f}, {actions[:, 1].max():.3f}]")
        print(f"    Z: [{actions[:, 2].min():.3f}, {actions[:, 2].max():.3f}]")

        print(f"\n  Rotation Range:")
        print(f"    Roll:  [{actions[:, 3].min():.3f}, {actions[:, 3].max():.3f}]")
        print(f"    Pitch: [{actions[:, 4].min():.3f}, {actions[:, 4].max():.3f}]")
        print(f"    Yaw:   [{actions[:, 5].min():.3f}, {actions[:, 5].max():.3f}]")

        print(f"\n  Gripper Statistics:")
        print(f"    Min:  {actions[:, 6].min():.3f}")
        print(f"    Max:  {actions[:, 6].max():.3f}")
        print(f"    Mean: {actions[:, 6].mean():.3f}")
    
    else:
        print(f"  Type: Unknown ({action_dim} DOF)")
        print(f"\n  Overall Range:")
        for i in range(action_dim):
            print(f"    Action {i}: [{actions[:, i].min():.3f}, {actions[:, i].max():.3f}]")

    print("\n" + "=" * 60 + "\n")


def main():
    """Main function for demonstration viewer."""
    parser = argparse.ArgumentParser(description="View and analyze recorded demonstrations.")
    parser.add_argument("demo_path", type=str, help="Path to demonstration file.")
    parser.add_argument("--plot", action="store_true", help="Show plots of the demonstration.")
    parser.add_argument("--save-plot", type=str, default=None, help="Save plot to file.")
    parser.add_argument("--list-keys", action="store_true", help="List all keys in the demonstration.")

    args = parser.parse_args()

    demo_path = Path(args.demo_path)
    if not demo_path.exists():
        print(f"Error: Demonstration file not found: {demo_path}")
        return

    print(f"Loading demonstration from: {demo_path}")
    demo = load_demonstration(str(demo_path))

    if args.list_keys:
        print("\nDemonstration Keys:")
        for key in demo.keys():
            if key == "metadata":
                print(f"  - {key}: {demo[key]}")
            else:
                print(f"  - {key}: shape={np.array(demo[key]).shape}")
        print()

    print_demo_stats(demo)

    if args.plot or args.save_plot:
        plot_demonstration(demo, args.save_plot)


if __name__ == "__main__":
    main()


