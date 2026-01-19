"""
OCR 辅助模块

提供基于 MaaFramework 的 OCR 功能，用于识别游戏中的数字和文本。
"""

import re
import logging
from typing import Optional, Tuple, List, Any

logger = logging.getLogger(__name__)

try:
    from maa.context import Context
    from maa.tasker import Tasker
    MAA_AVAILABLE = True
except ImportError:
    MAA_AVAILABLE = False
    logger.warning("MaaFramework not installed")


class OcrHelper:
    """
    OCR 辅助类
    
    使用 MaaFramework 的 Context.run_recognition 进行 OCR 识别。
    """
    
    def __init__(self, context: Optional['Context'] = None):
        """
        初始化 OCR 辅助类
        
        Args:
            context: MaaFramework Context 对象（可在 Custom Action 中获取）
        """
        self._context = context
    
    def set_context(self, context: 'Context'):
        """设置 Context"""
        self._context = context
    
    def recognize_text(
        self,
        roi: Tuple[int, int, int, int],
        expected: Optional[List[str]] = None,
        replace: Optional[List[Tuple[str, str]]] = None,
    ) -> Optional[str]:
        """
        识别指定区域的文本
        
        Args:
            roi: 识别区域 (x, y, w, h)
            expected: 期望的文本列表（用于过滤）
            replace: 文本替换规则 [(old, new), ...]
        
        Returns:
            识别到的文本，失败返回 None
        """
        if self._context is None:
            logger.warning("Context not set, cannot perform OCR")
            return None
        
        try:
            # 构建 OCR Pipeline 参数
            pipeline_override = {
                "OCR_Temp": {
                    "recognition": "OCR",
                    "roi": list(roi),
                    "only_rec": True,
                }
            }
            
            if expected:
                pipeline_override["OCR_Temp"]["expected"] = expected
            
            if replace:
                pipeline_override["OCR_Temp"]["replace"] = replace
            
            # 运行识别
            result = self._context.run_recognition(
                "OCR_Temp",
                self._context.tasker.controller.cached_image,
                pipeline_override
            )
            
            if result and result.detail:
                # 从 detail 中提取文本
                if isinstance(result.detail, dict):
                    return result.detail.get("text", "")
                elif isinstance(result.detail, str):
                    return result.detail
            
            return None
            
        except Exception as e:
            logger.error(f"OCR recognition failed: {e}")
            return None
    
    def recognize_int(
        self,
        roi: Tuple[int, int, int, int],
        default: int = 0
    ) -> int:
        """
        识别指定区域的数字
        
        Args:
            roi: 识别区域 (x, y, w, h)
            default: 识别失败时的默认值
        
        Returns:
            识别到的数字
        """
        text = self.recognize_text(
            roi,
            replace=[
                ("/", ""),  # 处理分数格式 "1/3"
                (",", ""),  # 移除千分位分隔符
                (" ", ""),  # 移除空格
            ]
        )
        
        if text is None:
            return default
        
        # 提取数字
        numbers = re.findall(r'\d+', text)
        if numbers:
            try:
                return int(numbers[0])
            except ValueError:
                return default
        
        return default
    
    def recognize_stage(self) -> Tuple[int, int]:
        """
        识别当前战斗阶段
        
        Returns:
            (current_stage, total_stage)，如 (1, 3)
        """
        # 当前阶段
        current = self.recognize_int((884, 14, 18, 23), default=1)
        # 总阶段
        total = self.recognize_int((912, 13, 20, 25), default=3)
        
        return current, total
    
    def recognize_enemy_hp(self, pos: int) -> int:
        """
        识别敌人血量
        
        Args:
            pos: 敌人位置 (0-5，前排0-2，后排3-5)
        
        Returns:
            敌人血量，识别失败返回 0
        """
        # 敌人血量 ROI（基于 720p）
        if pos < 3:
            # 前排敌人
            roi = (100 + 250 * pos, 40, 122, 25)
        else:
            # 后排敌人（位置需要调整）
            back_pos = pos - 3
            roi = (190 + back_pos * 200, 28, 97, 25)
        
        return self.recognize_int(roi, default=0)
    
    def recognize_servant_np(self, pos: int) -> int:
        """
        识别从者 NP 值
        
        Args:
            pos: 从者位置 (0-2)
        
        Returns:
            NP 值 (0-300)，识别失败返回 0
        """
        roi = (220 + 317 * pos, 655, 51, 25)
        return self.recognize_int(roi, default=0)
    
    def recognize_servant_hp(self, pos: int) -> int:
        """
        识别从者 HP 值
        
        Args:
            pos: 从者位置 (0-2)
        
        Returns:
            HP 值，识别失败返回 0
        """
        roi = (200 + 317 * pos, 620, 93, 24)
        return self.recognize_int(roi, default=0)
    
    def recognize_card_critical(self, pos: int) -> int:
        """
        识别卡牌暴击率
        
        Args:
            pos: 卡牌位置 (0-4)
        
        Returns:
            暴击率 (0-100)，识别失败返回 0
        """
        # 暴击率显示在卡牌上方
        roi = (80 + 257 * pos, 420, 60, 25)
        return self.recognize_int(roi, default=0)
    
    def recognize_team_index(self) -> int:
        """
        识别当前队伍编号
        
        Returns:
            队伍编号 (1-10)，识别失败返回 1
        """
        text = self.recognize_text(
            (452, 34, 376, 28),
            expected=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        )
        
        if text:
            try:
                return int(text)
            except ValueError:
                pass
        
        return 1


# 全局 OCR 辅助实例
_ocr_helper: Optional[OcrHelper] = None


def get_ocr_helper() -> OcrHelper:
    """获取全局 OCR 辅助实例"""
    global _ocr_helper
    if _ocr_helper is None:
        _ocr_helper = OcrHelper()
    return _ocr_helper


def set_ocr_context(context: 'Context'):
    """设置 OCR Context"""
    get_ocr_helper().set_context(context)
