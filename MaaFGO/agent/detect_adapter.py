"""
MaaDetectAdapter - 识别层适配器

将 FGO-py 的 fgoDetect 识别能力与 MaaFramework 的 Pipeline 系统集成。
支持两种使用方式：
1. 直接使用 MaaFramework 的内置识别算法（通过 Pipeline JSON）
2. 使用 FGO-py 的原有识别逻辑（通过 Custom Recognition）
"""

import cv2
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

try:
    from maa.context import Context
    from maa.custom_recognition import CustomRecognition
    MAA_AVAILABLE = True
except ImportError:
    MAA_AVAILABLE = False

from .ocr_helper import OcrHelper, get_ocr_helper, set_ocr_context


# 图像资源基础路径
IMAGE_BASE_PATH = Path(__file__).parent.parent / "resource" / "image"
FGO_IMAGE_PATH = Path(__file__).parent.parent.parent / "FGO-py" / "fgoImage"


class ImageLoader:
    """图像资源加载器"""
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or IMAGE_BASE_PATH
        self._cache: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}
    
    def load(self, name: str, region: str = "") -> Tuple[np.ndarray, np.ndarray]:
        """
        加载图像资源
        
        Args:
            name: 图像名称（不含扩展名）
            region: 区域（cn/jp/na/tw）
        
        Returns:
            (rgb, mask): RGB图像和掩码
        """
        cache_key = f"{region}/{name}" if region else name
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 尝试从 MaaFGO 资源加载
        if region:
            path = self.base_path / region / f"{name}.png"
        else:
            path = self.base_path / f"{name}.png"
        
        # 如果 MaaFGO 资源不存在，尝试从 FGO-py 加载
        if not path.exists():
            if region:
                path = FGO_IMAGE_PATH / region / f"{name}.png"
            else:
                path = FGO_IMAGE_PATH / f"{name}.png"
        
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {name}")
        
        img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise RuntimeError(f"Failed to load image: {path}")
        
        # 分离 RGB 和 Alpha 通道
        if img.shape[2] > 3:
            rgb = img[..., :3]
            mask = img[..., 3]
        else:
            rgb = img
            mask = np.ones((img.shape[0], img.shape[1]), dtype=np.uint8) * 255
        
        self._cache[cache_key] = (rgb, mask)
        return rgb, mask
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()


class MaaDetectAdapter:
    """
    MaaFramework 识别适配器
    
    提供与 fgoDetect 兼容的识别接口，同时支持 MaaFramework 的识别能力。
    """
    
    def __init__(self, screenshot_func=None, region: str = "CN", context: Optional['Context'] = None):
        """
        初始化识别适配器
        
        Args:
            screenshot_func: 截图函数（返回 BGR 图像）
            region: 游戏区域 (CN/JP/NA/TW)
            context: MaaFramework Context（用于 OCR）
        """
        self._screenshot_func = screenshot_func
        self._region = region.upper()
        self._image_loader = ImageLoader()
        self._im: Optional[np.ndarray] = None
        self._context = context
        self._ocr_helper = OcrHelper(context)
    
    def set_screenshot_func(self, func):
        """设置截图函数"""
        self._screenshot_func = func
    
    def set_region(self, region: str):
        """设置游戏区域"""
        self._region = region.upper()
    
    def set_context(self, context: 'Context'):
        """设置 MaaFramework Context（用于 OCR 等功能）"""
        self._context = context
        self._ocr_helper.set_context(context)
    
    def screenshot(self) -> np.ndarray:
        """截图并缓存"""
        if self._screenshot_func is None:
            raise RuntimeError("Screenshot function not set")
        self._im = self._screenshot_func()
        return self._im
    
    @property
    def image(self) -> Optional[np.ndarray]:
        """获取当前截图"""
        return self._im
    
    def inject(self, img: np.ndarray) -> "MaaDetectAdapter":
        """注入图像（用于调试）"""
        self._im = img
        return self
    
    def _crop(self, rect: Tuple[int, int, int, int]) -> np.ndarray:
        """裁剪图像区域"""
        x1, y1, x2, y2 = rect
        return self._im[y1:y2, x1:x2]
    
    def _load_template(self, name: str) -> Tuple[np.ndarray, np.ndarray]:
        """加载模板图像"""
        region = self._region.lower()
        try:
            return self._image_loader.load(name, region)
        except FileNotFoundError:
            return self._image_loader.load(name)
    
    def _match_template(
        self,
        template_name: str,
        roi: Tuple[int, int, int, int] = (0, 0, 1280, 720),
        threshold: float = 0.05
    ) -> Tuple[float, Tuple[int, int]]:
        """
        模板匹配
        
        Args:
            template_name: 模板名称
            roi: 搜索区域 (x1, y1, x2, y2)
            threshold: 匹配阈值
        
        Returns:
            (score, location): 匹配分数和位置
        """
        tmpl, mask = self._load_template(template_name)
        crop = self._crop(roi)
        
        result = cv2.matchTemplate(crop, tmpl, cv2.TM_SQDIFF_NORMED, mask=mask)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # 转换为绝对坐标
        abs_loc = (
            roi[0] + min_loc[0] + tmpl.shape[1] // 2,
            roi[1] + min_loc[1] + tmpl.shape[0] // 2
        )
        
        return min_val, abs_loc
    
    def _compare(
        self,
        template_name: str,
        roi: Tuple[int, int, int, int] = (0, 0, 1280, 720),
        threshold: float = 0.05
    ) -> bool:
        """
        比较是否匹配
        
        Args:
            template_name: 模板名称
            roi: 搜索区域
            threshold: 匹配阈值
        
        Returns:
            是否匹配
        """
        score, _ = self._match_template(template_name, roi, threshold)
        return score < threshold
    
    def _find(
        self,
        template_name: str,
        roi: Tuple[int, int, int, int] = (0, 0, 1280, 720),
        threshold: float = 0.05
    ) -> Optional[Tuple[int, int]]:
        """
        查找模板位置
        
        Returns:
            匹配位置或 None
        """
        score, loc = self._match_template(template_name, roi, threshold)
        return loc if score < threshold else None
    
    # ========== FGO 状态检测 API ==========
    
    def isMainInterface(self) -> bool:
        """检测是否在主界面"""
        return self._compare("menu", (1104, 613, 1267, 676))
    
    def isTurnBegin(self) -> bool:
        """检测是否回合开始（Attack 按钮可见）"""
        return self._compare("attack", (1155, 635, 1210, 682))
    
    def isBattleFormation(self) -> bool:
        """检测是否在编队界面"""
        return self._compare("battlebegin", (1070, 632, 1270, 710))
    
    def isBattleFinished(self) -> bool:
        """检测战斗是否结束（掉落界面）"""
        return self._compare("dropitem", (110, 30, 264, 76))
    
    def isBattleDefeated(self) -> bool:
        """检测是否战斗失败"""
        return self._compare("defeated", (603, 100, 690, 176))
    
    def isBattleContinue(self) -> bool:
        """检测是否可以继续战斗"""
        return self._compare("battlecontinue", (704, 530, 976, 618))
    
    def isNetworkError(self) -> bool:
        """检测网络错误"""
        return self._compare("networkerror", (703, 529, 974, 597))
    
    def isChooseFriend(self) -> bool:
        """检测是否在选择好友界面"""
        return self._compare("choosefriend", (1189, 190, 1210, 243))
    
    def isSkillReady(self, servant: int, skill: int) -> bool:
        """
        检测技能是否可用
        
        Args:
            servant: 从者位置 (0-2)
            skill: 技能位置 (0-2)
        """
        # 技能冷却标志检测
        roi = (35 + 318 * servant + 88 * skill, 598, 
               55 + 318 * servant + 88 * skill, 618)
        return not self._compare("still", roi, 0.2)
    
    def isHouguReady(self) -> List[bool]:
        """检测三个从者的宝具是否可用"""
        results = []
        for i in range(3):
            # 检测 NP 条
            roi = (144 + 319 * i, 679, 156 + 319 * i, 684)
            crop = self._crop(roi)
            mean_val = np.mean(crop)
            results.append(mean_val > 55)
        return results
    
    def getCardColor(self) -> List[int]:
        """
        获取卡牌颜色
        
        Returns:
            [0=Arts, 1=Quick, 2=Buster] 的列表
        """
        colors = []
        for i in range(5):
            roi = (80 + 257 * i, 537, 131 + 257 * i, 581)
            
            # 尝试匹配三种颜色
            scores = []
            for color in ["arts", "quick", "buster"]:
                try:
                    score, _ = self._match_template(color, roi)
                    scores.append(score)
                except FileNotFoundError:
                    scores.append(1.0)
            
            best = np.argmin(scores)
            colors.append(best if scores[best] < 0.2 else 0)
        
        return colors
    
    def getEnemyHp(self, pos: int) -> int:
        """
        获取敌人血量
        
        Args:
            pos: 敌人位置 (0-5)
        
        Returns:
            敌人血量，识别失败返回 0
        """
        # 敌人血量 ROI（基于 720p）
        if pos < 3:
            roi = (100 + 250 * pos, 40, 222 + 250 * pos, 65)
        else:
            # 后排敌人（如果存在）
            roi = (190 + (pos % 3) * 200 - (pos // 3) * 100, 28 + (pos // 3) * 99,
                   287 + (pos % 3) * 200 - (pos // 3) * 100, 53 + (pos // 3) * 99)
        
        try:
            return self._ocr_int(roi)
        except Exception:
            return 0
    
    def getStage(self) -> int:
        """获取当前关卡阶段"""
        try:
            return self._ocr_int((884, 14, 902, 37))
        except Exception:
            return 1
    
    def getStageTotal(self) -> int:
        """获取总关卡阶段数"""
        try:
            return self._ocr_int((912, 13, 932, 38))
        except Exception:
            return 3
    
    def getServantNp(self, pos: int) -> int:
        """
        获取从者 NP 值
        
        Args:
            pos: 从者位置 (0-2)
        
        Returns:
            NP 值 (0-300)
        """
        roi = (220 + 317 * pos, 655, 271 + 317 * pos, 680)
        try:
            return self._ocr_int(roi)
        except Exception:
            return 0
    
    def getServantHp(self, pos: int) -> int:
        """
        获取从者 HP 值
        
        Args:
            pos: 从者位置 (0-2)
        """
        roi = (200 + 317 * pos, 620, 293 + 317 * pos, 644)
        try:
            return self._ocr_int(roi)
        except Exception:
            return 0
    
    def _ocr_int(self, roi: Tuple[int, int, int, int]) -> int:
        """
        OCR 识别数字
        
        使用 MaaFramework 的 OCR 功能进行识别。
        如果 Context 未设置，则使用备用的简单识别方法。
        
        Args:
            roi: 识别区域 (x1, y1, x2, y2) 或 (x, y, w, h)
        
        Returns:
            识别到的数字，失败返回 0
        """
        # 转换 roi 格式：如果是 (x1, y1, x2, y2) 需要转为 (x, y, w, h)
        if len(roi) == 4:
            x1, y1, x2, y2 = roi
            # 判断是 (x1, y1, x2, y2) 还是 (x, y, w, h)
            if x2 > x1 + 50 and y2 > y1 + 10:
                # 可能是 (x1, y1, x2, y2)，转换为 (x, y, w, h)
                roi_xywh = (x1, y1, x2 - x1, y2 - y1)
            else:
                # 已经是 (x, y, w, h)
                roi_xywh = roi
        else:
            roi_xywh = roi
        
        # 优先使用 MaaFramework OCR
        if self._context is not None:
            return self._ocr_helper.recognize_int(roi_xywh, default=0)
        
        # 备用方法：使用 OpenCV 进行简单识别
        return self._ocr_int_fallback(roi)
    
    def _ocr_int_fallback(self, roi: Tuple[int, int, int, int]) -> int:
        """
        备用 OCR 方法：使用 OpenCV 进行简单数字识别
        
        注意：这是一个非常简化的实现，识别准确率较低。
        建议在正式使用时配置 MaaFramework Context 以使用完整 OCR。
        """
        try:
            # 确保是 (x1, y1, x2, y2) 格式
            x1, y1, x2, y2 = roi
            if x2 <= x1 or y2 <= y1:
                # 可能是 (x, y, w, h) 格式，转换
                x2 = x1 + x2
                y2 = y1 + y2
            
            crop = self._crop((x1, y1, x2, y2))
            
            if crop is None or crop.size == 0:
                return 0
            
            # 转灰度
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            
            # 二值化
            _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
            
            # 使用轮廓数量估算数字
            # 这只是一个非常粗略的估算
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 返回 0 表示无法识别
            logger.debug(f"OCR fallback: found {len(contours)} contours, returning 0")
            return 0
            
        except Exception as e:
            logger.warning(f"OCR fallback failed: {e}")
            return 0


# ========== Custom Recognition 注册 ==========
# 使用统一的 ResourceManager
try:
    from custom.resource_manager import custom_recognition
except ImportError:
    # 如果无法导入，定义一个空装饰器
    def custom_recognition(name):
        def decorator(cls):
            return cls
        return decorator

if MAA_AVAILABLE:
    
    @custom_recognition("FGO_MainInterface")
    class FGOMainInterfaceRecognition(CustomRecognition):
        """检测主界面"""
        
        def analyze(self, context: Context, argv) -> CustomRecognition.AnalyzeResult:
            image = argv.image
            adapter = MaaDetectAdapter()
            adapter.inject(image)
            
            if adapter.isMainInterface():
                return CustomRecognition.AnalyzeResult(
                    box=(1104, 613, 163, 63),
                    detail="Main interface detected"
                )
            return None
    
    @custom_recognition("FGO_TurnBegin")
    class FGOTurnBeginRecognition(CustomRecognition):
        """检测回合开始"""
        
        def analyze(self, context: Context, argv) -> CustomRecognition.AnalyzeResult:
            image = argv.image
            adapter = MaaDetectAdapter()
            adapter.inject(image)
            
            if adapter.isTurnBegin():
                return CustomRecognition.AnalyzeResult(
                    box=(1155, 635, 55, 47),
                    detail="Turn begin detected"
                )
            return None
    
    @custom_recognition("FGO_BattleFinished")
    class FGOBattleFinishedRecognition(CustomRecognition):
        """检测战斗结束"""
        
        def analyze(self, context: Context, argv) -> CustomRecognition.AnalyzeResult:
            image = argv.image
            adapter = MaaDetectAdapter()
            adapter.inject(image)
            
            if adapter.isBattleFinished():
                return CustomRecognition.AnalyzeResult(
                    box=(110, 30, 154, 46),
                    detail="Battle finished"
                )
            return None
    
    @custom_recognition("FGO_CardColor")
    class FGOCardColorRecognition(CustomRecognition):
        """识别卡牌颜色"""
        
        def analyze(self, context: Context, argv) -> CustomRecognition.AnalyzeResult:
            image = argv.image
            adapter = MaaDetectAdapter()
            adapter.inject(image)
            
            try:
                colors = adapter.getCardColor()
                return CustomRecognition.AnalyzeResult(
                    box=(0, 0, 1280, 720),
                    detail={"colors": colors, "names": ["Arts", "Quick", "Buster"]}
                )
            except Exception as e:
                return CustomRecognition.AnalyzeResult(
                    box=(0, 0, 1280, 720),
                    detail={"error": str(e)}
                )
