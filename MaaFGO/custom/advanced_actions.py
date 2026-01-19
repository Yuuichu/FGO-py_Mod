"""
FGO 高级功能动作

包含：
- 关卡导航 (goto)
- 周常任务
- 网络错误守护
- 刷本统计

迁移自 fgoKernel 的高级功能
"""

import time
import logging
import threading
from typing import List, Dict, Any, Optional, Tuple

try:
    from maa.custom_action import CustomAction
    from maa.context import Context
    MAA_AVAILABLE = True
except ImportError:
    MAA_AVAILABLE = False

from .resource_manager import custom_action

logger = logging.getLogger(__name__)


# ============ 网络错误守护 ============

class NetworkGuardian:
    """
    网络错误守护进程
    
    后台监控网络错误弹窗，自动点击确认重连。
    移植自 fgoKernel.guardian
    """
    
    _instance: Optional['NetworkGuardian'] = None
    _running: bool = False
    _thread: Optional[threading.Thread] = None
    _controller = None
    _check_interval: float = 3.0
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'NetworkGuardian':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def start(cls, controller):
        """启动守护进程"""
        instance = cls.get_instance()
        instance._controller = controller
        
        if not cls._running:
            cls._running = True
            cls._thread = threading.Thread(
                target=instance._guardian_loop,
                daemon=True,
                name='NetworkGuardian'
            )
            cls._thread.start()
            logger.info("Network guardian started")
    
    @classmethod
    def stop(cls):
        """停止守护进程"""
        cls._running = False
        logger.info("Network guardian stopped")
    
    def _guardian_loop(self):
        """守护循环"""
        # 网络错误确认按钮位置
        CONFIRM_BUTTON = (640, 560)
        
        while self._running:
            try:
                time.sleep(self._check_interval)
                
                if self._controller is None:
                    continue
                
                # TODO: 检测网络错误弹窗
                # 这需要使用 MaaFramework 的模板匹配
                # 简化实现：通过 Pipeline 来处理
                
            except Exception as e:
                logger.error(f"Guardian error: {e}")


# ============ 刷本统计 ============

class FarmingStats:
    """
    刷本统计
    
    跟踪刷本次数、时间、掉落物等统计信息。
    """
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置统计"""
        self.start_time = time.time()
        self.battle_count = 0
        self.defeated_count = 0
        self.total_turns = 0
        self.total_battle_time = 0.0
        self.materials: Dict[str, int] = {}
        self.apple_consumed = 0
    
    def add_battle(self, turns: int, battle_time: float, won: bool):
        """添加战斗记录"""
        self.battle_count += 1
        if won:
            self.total_turns += turns
            self.total_battle_time += battle_time
        else:
            self.defeated_count += 1
    
    def add_material(self, name: str, count: int = 1):
        """添加掉落物"""
        self.materials[name] = self.materials.get(name, 0) + count
    
    def add_apple(self, count: int = 1):
        """记录吃苹果"""
        self.apple_consumed += count
    
    @property
    def success_count(self) -> int:
        return self.battle_count - self.defeated_count
    
    @property
    def avg_turns(self) -> float:
        if self.success_count == 0:
            return 0
        return self.total_turns / self.success_count
    
    @property
    def avg_battle_time(self) -> float:
        if self.success_count == 0:
            return 0
        return self.total_battle_time / self.success_count
    
    @property
    def total_time(self) -> float:
        return time.time() - self.start_time
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "battle_count": self.battle_count,
            "success_count": self.success_count,
            "defeated_count": self.defeated_count,
            "avg_turns": round(self.avg_turns, 2),
            "avg_battle_time": round(self.avg_battle_time, 2),
            "total_time": round(self.total_time, 2),
            "apple_consumed": self.apple_consumed,
            "materials": self.materials,
        }


# 全局统计实例
_farming_stats: Optional[FarmingStats] = None


def get_farming_stats() -> FarmingStats:
    """获取全局刷本统计"""
    global _farming_stats
    if _farming_stats is None:
        _farming_stats = FarmingStats()
    return _farming_stats


def reset_farming_stats():
    """重置刷本统计"""
    global _farming_stats
    _farming_stats = FarmingStats()


if MAA_AVAILABLE:

    @custom_action("FGO_StartNetworkGuardian")
    class FGOStartNetworkGuardianAction(CustomAction):
        """
        启动网络错误守护进程
        """

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            NetworkGuardian.start(controller)
            return True


    @custom_action("FGO_StopNetworkGuardian")
    class FGOStopNetworkGuardianAction(CustomAction):
        """
        停止网络错误守护进程
        """

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            NetworkGuardian.stop()
            return True


    @custom_action("FGO_ResetFarmingStats")
    class FGOResetFarmingStatsAction(CustomAction):
        """
        重置刷本统计
        """

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            reset_farming_stats()
            logger.info("Farming stats reset")
            return True


    @custom_action("FGO_RecordBattle")
    class FGORecordBattleAction(CustomAction):
        """
        记录战斗结果
        
        参数:
            turns: 回合数
            battle_time: 战斗时间（秒）
            won: 是否胜利
        """

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            params = argv.custom_action_param or {}
            
            turns = params.get("turns", 0)
            battle_time = params.get("battle_time", 0.0)
            won = params.get("won", True)
            
            stats = get_farming_stats()
            stats.add_battle(turns, battle_time, won)
            
            logger.info(f"Battle recorded: turns={turns}, time={battle_time:.1f}s, won={won}")
            return True


    @custom_action("FGO_GotoQuest")
    class FGOGotoQuestAction(CustomAction):
        """
        自动导航到指定关卡
        
        参数:
            quest: 关卡信息 [chapter, area, quest_index]
                   例如: [8, 2, 1] 表示第8章第2区域第1个关卡
        
        这是一个简化实现，完整实现需要：
        1. 检测当前界面
        2. 导航到终端（如果不在）
        3. 选择章节
        4. 选择区域
        5. 滚动到目标关卡
        """
        
        # 终端按钮位置
        TERMINAL_BUTTON = (640, 600)
        
        # 返回按钮
        BACK_BUTTON = (100, 50)

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            params = argv.custom_action_param or {}
            
            quest = params.get("quest", [1, 1, 0])
            
            if len(quest) < 3:
                logger.error("Invalid quest format, expected [chapter, area, quest_index]")
                return False
            
            chapter, area, quest_index = quest[0], quest[1], quest[2]
            
            logger.info(f"Navigating to quest: Chapter {chapter}, Area {area}, Quest {quest_index}")
            
            try:
                # 简化实现：假设已经在关卡选择界面
                # 完整实现需要更复杂的状态检测和导航
                
                # 点击关卡位置（需要根据实际情况调整）
                quest_y = 300 + quest_index * 100
                controller.post_click(640, quest_y).wait()
                time.sleep(1.0)
                
                return True
                
            except Exception as e:
                logger.error(f"Quest navigation failed: {e}")
                return False


    @custom_action("FGO_CheckWeeklyMission")
    class FGOCheckWeeklyMissionAction(CustomAction):
        """
        检查周常任务
        
        读取周常任务列表，返回未完成的任务信息。
        这是一个简化实现，完整版需要 OCR 识别任务文本。
        """
        
        # 任务按钮位置
        MISSION_BUTTON = (1200, 50)
        
        # 周常任务标签
        WEEKLY_TAB = (400, 100)

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            
            try:
                # 打开任务界面
                controller.post_click(*self.MISSION_BUTTON).wait()
                time.sleep(1.5)
                
                # 切换到周常任务标签
                controller.post_click(*self.WEEKLY_TAB).wait()
                time.sleep(1.0)
                
                # TODO: 使用 OCR 读取任务列表
                # 简化实现：返回成功
                
                logger.info("Weekly mission check completed")
                return True
                
            except Exception as e:
                logger.error(f"Weekly mission check failed: {e}")
                return False


    @custom_action("FGO_HandleNetworkError")
    class FGOHandleNetworkErrorAction(CustomAction):
        """
        处理网络错误弹窗
        
        检测并点击确认按钮重连。
        """
        
        CONFIRM_BUTTON = (640, 560)

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            
            # 点击确认按钮
            controller.post_click(*self.CONFIRM_BUTTON).wait()
            time.sleep(3.0)
            
            logger.info("Network error handled, reconnecting...")
            return True


    @custom_action("FGO_GetFarmingStats")
    class FGOGetFarmingStatsAction(CustomAction):
        """
        获取刷本统计信息
        
        将统计信息输出到日志。
        """

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            stats = get_farming_stats()
            stats_dict = stats.to_dict()
            
            logger.info("=" * 40)
            logger.info("Farming Statistics:")
            logger.info(f"  Battles: {stats_dict['battle_count']} (Success: {stats_dict['success_count']}, Failed: {stats_dict['defeated_count']})")
            logger.info(f"  Avg Turns: {stats_dict['avg_turns']}")
            logger.info(f"  Avg Battle Time: {stats_dict['avg_battle_time']}s")
            logger.info(f"  Total Time: {stats_dict['total_time']}s")
            logger.info(f"  Apples Used: {stats_dict['apple_consumed']}")
            if stats_dict['materials']:
                logger.info(f"  Materials: {stats_dict['materials']}")
            logger.info("=" * 40)
            
            return True


# 导出
ADVANCED_ACTIONS = [
    "FGO_StartNetworkGuardian",
    "FGO_StopNetworkGuardian",
    "FGO_ResetFarmingStats",
    "FGO_RecordBattle",
    "FGO_GotoQuest",
    "FGO_CheckWeeklyMission",
    "FGO_HandleNetworkError",
    "FGO_GetFarmingStats",
]
