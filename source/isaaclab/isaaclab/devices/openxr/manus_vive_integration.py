"""Python wrapper for a custom manus IsaacLab bridge."""

import ctypes
from typing import Dict, List


class ManusViveIntegration:
    """Python interface to the Manus Vive SDK bridge for IsaacLab.
    
    This class provides a ctypes-based interface to a C++ bridge that
    communicates with the Manus SDK to retrieve hand tracking data from
    Manus gloves. The data is returned in a format compatible with IsaacLab's
    device interface.
    
    Attributes:
        _bridge_lib: The loaded shared library handle.
        _pose_buffer: Pre-allocated buffer for receiving pose data.
        _MAX_NUM_NODES: Maximum number of nodes (joints) that can be tracked.
    """
    def __init__(self):
        # Load the shared library
        self._bridge_lib = ctypes.CDLL("libmanus-vive-isaaclab-bridge.so")
        
        # Define structures to match C++ layout
        class _ManusVec3(ctypes.Structure):
            _fields_ = [
                ("x", ctypes.c_float),
                ("y", ctypes.c_float),
                ("z", ctypes.c_float),
            ]

        class _ManusQuaternion(ctypes.Structure):
            _fields_ = [
                ("w", ctypes.c_float),
                ("x", ctypes.c_float),
                ("y", ctypes.c_float),
                ("z", ctypes.c_float),
            ]

        class _ManusNodePose(ctypes.Structure):
            _fields_ = [
                ("glove_id", ctypes.c_uint32),
                ("node_id", ctypes.c_uint32),
                ("side", ctypes.c_uint32),
                ("position", _ManusVec3),
                ("orientation", _ManusQuaternion),
            ]

        self._ManusNodePose = _ManusNodePose
        self._MAX_NUM_NODES = 512
        self._pose_buffer = (_ManusNodePose * self._MAX_NUM_NODES)()
        
        # Define C function signatures
        # bridge_create() -> Bridge*
        self._bridge_lib.bridge_create.argtypes = []
        self._bridge_lib.bridge_create.restype = ctypes.c_void_p
        
        # poll(ManusNodePose* buffer, uint32_t buffer_size, uint32_t* count) -> int
        self._bridge_lib.poll.argtypes = [
            ctypes.POINTER(_ManusNodePose),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32)
        ]
        self._bridge_lib.poll.restype = ctypes.c_int
        
        # shutdown() -> int
        self._bridge_lib.shutdown.argtypes = []
        self._bridge_lib.shutdown.restype = ctypes.c_int
        
        # Create and initialize the bridge
        bridge_ptr = self._bridge_lib.bridge_create()
        if not bridge_ptr:
            raise RuntimeError("Failed to create and initialize Manus Vive bridge")

    def get_all_device_data(self) -> dict:
        """Get all tracked device data in scene coordinates in a format compatible with manus_vive.py.

        Returns:
            Manus glove joint data.
            {
                'manus_gloves': {
                    '{left/right}_{joint_index}': {
                        'position': [x, y, z],
                        'orientation': [w, x, y, z]
                    },
                    ...
                }
            }
        """
        num_nodes = self.poll_current_bridge_data_into_buffer()
        return {"manus_gloves": self.map_buffer_data_to_dict(num_nodes)}

    def poll_current_bridge_data_into_buffer(self):
        """Poll the bridge for new skeleton data and update the internal buffer.
        
        Returns:
            Number of nodes retrieved.
        
        Raises:
            RuntimeError: If polling fails with an error other than "no data" (-2).
        """
        count = ctypes.c_uint32(0)
        result = self._bridge_lib.poll(
            self._pose_buffer, 
            self._MAX_NUM_NODES, 
            ctypes.byref(count)
        )
        
        # Return codes: 0 = success, -1 = not initialized, -2 = no data, -3 = invalid args
        if result == -1:
            raise RuntimeError("Manus Vive bridge not initialized")
        elif result == -3:
            raise RuntimeError("Invalid arguments passed to poll function")
        elif result != 0 and result != -2:
            raise RuntimeError(f"Failed to poll Manus Vive bridge data (error code: {result})")
            
        return count.value

    def map_buffer_data_to_dict(self, num_nodes: int) -> Dict[str, Dict[str, List[float]]]:
        """Convert the internal buffer data to a dictionary format.
        
        Args:
            num_nodes: Number of valid nodes in the buffer.
            
        Returns:
            Dictionary mapping node keys to their pose data. Each node key is
            formatted as "{side}_{node_id}" where side is "left", "right", or "unknown".
            Each pose contains "position" (x, y, z) and "orientation" (w, x, y, z).
        """
        mapped: Dict[str, Dict[str, List[float]]] = {}
        
        for idx in range(num_nodes):
            pose = self._pose_buffer[idx]
            
            # Map side enum to string: 1 = left, 2 = right
            if pose.side == 1:
                side_prefix = "left"
            elif pose.side == 2:
                side_prefix = "right"
            else:
                side_prefix = "unknown"
            
            key = f"{side_prefix}_{pose.node_id}"
            mapped[key] = {
                "position": [pose.position.x, pose.position.y, pose.position.z],
                "orientation": [
                    pose.orientation.w,
                    pose.orientation.x,
                    pose.orientation.y,
                    pose.orientation.z,
                ],
            }
            
        return mapped

    def shutdown(self):
        """Shutdown the Manus Vive bridge and disconnect from the SDK.
        
        Raises:
            RuntimeError: If shutdown fails.
        """
        result = self._bridge_lib.shutdown()
        if result != 0:
            raise RuntimeError(f"Failed to shutdown Manus Vive bridge (error code: {result})")
