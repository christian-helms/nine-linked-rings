from dataclasses import dataclass
from typing import Callable

from isaaclab.devices.device_base import DeviceCfg
from isaaclab.devices.device_base import DeviceBase
from isaaclab.devices.openxr.xr_cfg import XrCfg
from isaaclab.devices.retargeter_base import RetargeterBase

from geort.mocap.manus_mocap import ManusMocap

@dataclass
class ManusViveGeortDeviceCfg(DeviceCfg):
    xr_cfg: XrCfg | None = None

class ManusViveGeortDevice(DeviceBase):
    def __init__(self, cfg: ManusViveGeortDeviceCfg, retargeters: list[RetargeterBase] | None = None):
        super().__init__(retargeters)
        self.mocap_device = ManusMocap()
        self.xr_cfg = cfg.xr_cfg or XrCfg()
        self._additional_callbacks = dict()

    def _get_raw_data(self) -> dict:
        return self.mocap_device.get()

    def reset(self):
        pass

    def add_callback(self, key: str, func: Callable):
        self._additional_callbacks[key] = func