"""
MaaDeviceAdapter - 设备控制层适配器

用 MaaFramework 的 AdbController/Win32Controller 替代 FGO-py 的 fgoDevice，
提供统一的设备控制接口。
"""

import time
import numpy as np
from typing import Optional, Tuple, Union
from pathlib import Path

try:
    from maa.controller import AdbController, Win32Controller
    from maa.toolkit import Toolkit
    from maa.define import MaaAdbScreencapMethodEnum, MaaAdbInputMethodEnum
    MAA_AVAILABLE = True
except ImportError:
    MAA_AVAILABLE = False
    print("Warning: MaaFramework not installed. Run: pip install MaaFw")


class MaaDeviceAdapter:
    """
    MaaFramework 设备控制适配器
    
    提供与 fgoDevice.Device 兼容的接口：
    - screenshot(): 截图
    - touch(pos, wait): 触摸
    - press(key): 按键
    - swipe(start, end): 滑动
    - perform(keys, waits): 批量操作
    """
    
    def __init__(
        self,
        adb_path: Optional[str] = None,
        address: Optional[str] = None,
        hwnd: Optional[int] = None,
        screenshot_short_side: int = 720,
    ):
        """
        初始化设备适配器
        
        Args:
            adb_path: ADB 路径（可选，自动检测）
            address: ADB 连接地址（如 127.0.0.1:5555）
            hwnd: Windows 窗口句柄（用于 Win32 控制）
            screenshot_short_side: 截图短边尺寸（默认 720）
        """
        if not MAA_AVAILABLE:
            raise RuntimeError("MaaFramework not installed")
        
        self._controller = None
        self._connected = False
        self._screenshot_short_side = screenshot_short_side
        self._last_screenshot = None
        self._name = ""
        
        if hwnd is not None:
            self._init_win32(hwnd)
        elif address is not None:
            self._init_adb(adb_path, address)
    
    def _init_adb(self, adb_path: Optional[str], address: str):
        """初始化 ADB 控制器"""
        # 如果没有指定 adb_path，使用 Toolkit 自动检测
        if adb_path is None:
            Toolkit.init_option(".")
            devices = Toolkit.find_adb_devices()
            if not devices:
                raise RuntimeError("No ADB devices found")
            # 查找匹配的设备
            device = next((d for d in devices if d.address == address), devices[0])
            adb_path = device.adb_path
            address = device.address
        
        self._controller = AdbController(
            adb_path=adb_path,
            address=address,
            screencap_methods=MaaAdbScreencapMethodEnum.Default,
            input_methods=MaaAdbInputMethodEnum.Default,
        )
        
        # 设置截图目标尺寸
        self._controller.set_screenshot_target_short_side(self._screenshot_short_side)
        
        self._name = f"adb:{address}"
    
    def _init_win32(self, hwnd: int):
        """初始化 Win32 控制器"""
        self._controller = Win32Controller(hWnd=hwnd)
        self._controller.set_screenshot_target_short_side(self._screenshot_short_side)
        self._name = f"win32:{hwnd}"
    
    def connect(self) -> bool:
        """连接设备"""
        if self._controller is None:
            return False
        
        job = self._controller.post_connection()
        status = job.wait()
        self._connected = status.succeeded()
        return self._connected
    
    @property
    def connected(self) -> bool:
        """是否已连接"""
        return self._connected and self._controller is not None
    
    @property
    def available(self) -> bool:
        """设备是否可用（兼容 fgoDevice）"""
        return self.connected
    
    @property
    def name(self) -> str:
        """设备名称"""
        return self._name
    
    def screenshot(self) -> np.ndarray:
        """
        截图
        
        Returns:
            numpy.ndarray: BGR 格式的截图图像
        """
        if not self.connected:
            raise RuntimeError("Device not connected")
        
        job = self._controller.post_screencap()
        self._last_screenshot = job.wait().get()
        return self._last_screenshot
    
    @property
    def cached_image(self) -> Optional[np.ndarray]:
        """获取最后一次截图"""
        return self._last_screenshot
    
    def touch(self, pos: Tuple[int, int], wait: float = 0):
        """
        触摸操作（兼容 fgoDevice）
        
        Args:
            pos: 触摸位置 (x, y)
            wait: 等待时间（毫秒）
        """
        if not self.connected:
            raise RuntimeError("Device not connected")
        
        self._controller.post_click(int(pos[0]), int(pos[1])).wait()
        if wait > 0:
            time.sleep(wait / 1000)
    
    def click(self, x: int, y: int):
        """点击操作"""
        self.touch((x, y))
    
    def press(self, key: str):
        """
        按键操作（兼容 fgoDevice）
        
        Args:
            key: 按键字符
        """
        if not self.connected:
            raise RuntimeError("Device not connected")
        
        # 将 FGO-py 的按键映射到触摸坐标
        # 这里需要根据实际游戏界面调整
        key_map = {
            ' ': (640, 400),      # 空格 -> 屏幕中央
            'K': (640, 600),      # K -> 确认按钮
            '1': (128, 500),      # 卡牌1
            '2': (385, 500),      # 卡牌2
            '3': (642, 500),      # 卡牌3
            '4': (899, 500),      # 卡牌4
            '5': (1156, 500),     # 卡牌5
            '6': (318, 250),      # 宝具1
            '7': (640, 250),      # 宝具2
            '8': (962, 250),      # 宝具3
            # 技能按键
            'A': (88, 592),       # 从者1技能1
            'S': (176, 592),      # 从者1技能2
            'D': (264, 592),      # 从者1技能3
            'F': (406, 592),      # 从者2技能1
            'G': (494, 592),      # 从者2技能2
            'H': (582, 592),      # 从者2技能3
            'J': (724, 592),      # 从者3技能1
            'K': (812, 592),      # 从者3技能2
            'L': (900, 592),      # 从者3技能3
            'Q': (1200, 340),     # 御主技能
            'W': (1000, 430),     # 御主技能1
            'E': (1100, 430),     # 御主技能2
            'R': (1200, 430),     # 御主技能3
            # 返回
            '\x08': (100, 50),    # 退格 -> 返回按钮
            '\xBB': (1200, 50),   # 跳过按钮
        }
        
        if key in key_map:
            self.touch(key_map[key])
        else:
            # 尝试作为输入文本
            self._controller.post_input_text(key).wait()
    
    def swipe(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        duration: int = 500
    ):
        """
        滑动操作
        
        Args:
            start: 起点 (x, y)
            end: 终点 (x, y)
            duration: 滑动时长（毫秒）
        """
        if not self.connected:
            raise RuntimeError("Device not connected")
        
        self._controller.post_swipe(
            int(start[0]), int(start[1]),
            int(end[0]), int(end[1]),
            duration
        ).wait()
    
    def perform(self, keys: str, waits: Tuple[int, ...]):
        """
        批量操作（兼容 fgoDevice）
        
        Args:
            keys: 按键序列
            waits: 每个按键后的等待时间（毫秒）
        """
        for key, wait in zip(keys, waits):
            self.press(key)
            if wait > 0:
                time.sleep(wait / 1000)
    
    def __del__(self):
        """清理资源"""
        self._controller = None


def find_adb_devices():
    """
    查找可用的 ADB 设备
    
    Returns:
        list: 设备列表 [(name, address, adb_path), ...]
    """
    if not MAA_AVAILABLE:
        return []
    
    Toolkit.init_option(".")
    devices = Toolkit.find_adb_devices()
    return [(d.name, d.address, d.adb_path) for d in devices]


def find_win32_windows():
    """
    查找可用的 Win32 窗口
    
    Returns:
        list: 窗口列表 [(title, hwnd), ...]
    """
    if not MAA_AVAILABLE:
        return []
    
    Toolkit.init_option(".")
    windows = Toolkit.find_desktop_windows()
    return [(w.window_name, w.hwnd) for w in windows]


# 单例设备实例（兼容 fgoDevice.device）
_device_instance: Optional[MaaDeviceAdapter] = None


def get_device() -> Optional[MaaDeviceAdapter]:
    """获取全局设备实例"""
    return _device_instance


def set_device(device: MaaDeviceAdapter):
    """设置全局设备实例"""
    global _device_instance
    _device_instance = device


def connect_device(address: str = None, hwnd: int = None) -> MaaDeviceAdapter:
    """
    便捷函数：连接设备并设置为全局实例
    
    Args:
        address: ADB 连接地址
        hwnd: Windows 窗口句柄
    
    Returns:
        MaaDeviceAdapter: 设备实例
    """
    if address:
        device = MaaDeviceAdapter(address=address)
    elif hwnd:
        device = MaaDeviceAdapter(hwnd=hwnd)
    else:
        # 自动检测第一个设备
        devices = find_adb_devices()
        if devices:
            _, address, adb_path = devices[0]
            device = MaaDeviceAdapter(adb_path=adb_path, address=address)
        else:
            raise RuntimeError("No devices found")
    
    if device.connect():
        set_device(device)
        return device
    else:
        raise RuntimeError("Failed to connect device")
