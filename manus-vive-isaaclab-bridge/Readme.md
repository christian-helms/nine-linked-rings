# MANUS-Vive IsaacLab Bridge

A C++ bridge library that connects the Manus SDK to IsaacLab via Python ctypes, enabling real-time hand tracking data from Manus gloves equipped with trackers in Isaac Lab simulations.

## Overview

This library provides:
- C++ bridge to the Manus SDK for retrieving hand skeleton data
- C interface compatible with Python ctypes
- Thread-safe data polling mechanism
- Automatic connection to Manus Core

## Requirements

- C++17 compatible compiler (g++)
- Manus SDK (included in `ManusSDK/`)
- ncurses library
- Root/sudo access for installation

## Building

Build the shared library:

```bash
make
```

For debug build with debug symbols:

```bash
make debug
```

To clean build artifacts:

```bash
make clean
```

## Installation

Install the library to `/usr/lib` (requires sudo):

```bash
make install
```

This will:
- Copy `libmanus-vive-isaaclab-bridge.so` to `/usr/lib/`
- Copy Manus SDK libraries to `/usr/lib/manus/`
- Update the library cache with `ldconfig`

## Uninstallation

To remove the installed library:

```bash
make uninstall
```

## Usage in Python

Once installed, you can use the library in Python via the `ManusViveIntegration` class:

```python
from isaaclab.devices.openxr.manus_vive_integration import ManusViveIntegration

# Initialize the bridge (connects to Manus Core automatically)
bridge = ManusViveIntegration()

# Poll for hand tracking data
data = bridge.get_all_device_data()

# Data format:
# {
#     'left_0': {'position': [x, y, z], 'orientation': [w, x, y, z]},
#     'left_1': {'position': [x, y, z], 'orientation': [w, x, y, z]},
#     ...
# }

# Shutdown when done
bridge.shutdown()
```

## Architecture

- **Bridge Class (C++)**: Manages connection to Manus Core and SDK callbacks
- **C Interface**: Provides `extern "C"` functions for Python ctypes
- **Thread Safety**: Mutex-protected double-buffering for callback data
- **Python Wrapper**: ctypes-based interface with proper type definitions

## Return Codes

The C interface functions return integer status codes:

- `0`: Success
- `-1`: Not initialized
- `-2`: No data available (not an error)
- `-3`: Invalid arguments

## Troubleshooting

### Library not found
If Python can't find the library after installation, ensure `/usr/lib` is in your library path:
```bash
sudo ldconfig
```

### Connection failures
Ensure Manus Core is running before initializing the bridge. The bridge will retry connection automatically with 1-second intervals.

### Buffer overflow warnings
If you see buffer overflow messages, the default buffer size (512 nodes) may be insufficient. Increase `_MAX_NUM_NODES` in the Python wrapper.

## Technical Details

- **Coordinate System**: Z-up, X-forward, right-handed, meters
- **Hand Motion Mode**: Tracker (using external VR tracker data)
- **Max Nodes**: 512 (configurable in Python wrapper)
