"""
MaaFGO Agent - MaaFramework 与 FGO-py 集成模块

本模块提供 MaaFramework 与 FGO-py 的桥接层，包括：
- MaaDeviceAdapter: 设备控制层适配器
- MaaDetectAdapter: 识别层适配器
- OcrHelper: OCR 辅助工具
- Custom Recognition/Action: 战斗逻辑扩展
"""

from .device_adapter import MaaDeviceAdapter
from .detect_adapter import MaaDetectAdapter
from .ocr_helper import OcrHelper, get_ocr_helper, set_ocr_context

__all__ = [
    "MaaDeviceAdapter",
    "MaaDetectAdapter",
    "OcrHelper",
    "get_ocr_helper",
    "set_ocr_context",
]
