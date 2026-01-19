"""
FGO 实用功能的自定义动作
包括：抽奖、合成、好友选择等
"""

import time
import random
from typing import List, Tuple

try:
    from maa.custom_action import CustomAction
    from maa.context import Context
    MAA_AVAILABLE = True
except ImportError:
    MAA_AVAILABLE = False

# 使用统一的 Resource 管理器
from .resource_manager import custom_action

if MAA_AVAILABLE:

    @custom_action("FGO_LotteryRoll")
    class FGOLotteryRollAction(CustomAction):
        """
        抽奖动作
        
        参数:
            times: 抽奖次数 (默认 10)
        """
        
        # 抽奖按钮
        ROLL_BUTTON = (640, 660)

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            params = argv.custom_action_param or {}
            
            times = params.get("times", 10)
            
            for _ in range(times):
                # 添加随机延迟，模拟人工操作
                delay = random.randint(100, 300)
                controller.post_click(*self.ROLL_BUTTON).wait()
                time.sleep(delay / 1000)
            
            return True


    @custom_action("FGO_SelectSynthesisCards")
    class FGOSelectSynthesisCardsAction(CustomAction):
        """
        选择合成素材卡
        自动选择一页的素材卡（最多28张）
        """
        
        # 卡片位置矩阵 (4行7列)
        CARD_GRID = [
            [(133 + 133 * j, 253 + 142 * i) for j in range(7)]
            for i in range(4)
        ]

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            params = argv.custom_action_param or {}
            
            # 展开选择
            controller.post_click(640, 200).wait()
            time.sleep(1.0)
            
            # 选择所有卡片
            for row in self.CARD_GRID:
                for pos in row:
                    controller.post_click(*pos).wait()
                    time.sleep(0.1)
            
            return True


    @custom_action("FGO_ScrollFriendList")
    class FGOScrollFriendListAction(CustomAction):
        """
        滚动好友列表
        """

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            
            # 向下滚动
            controller.post_swipe(400, 600, 400, 200, 500).wait()
            time.sleep(0.4)
            
            return True


    @custom_action("FGO_RefreshFriendList")
    class FGORefreshFriendListAction(CustomAction):
        """
        刷新好友列表
        """
        
        # 刷新按钮
        REFRESH_BUTTON = (1200, 130)
        # 确认按钮
        CONFIRM_BUTTON = (640, 560)

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            
            # 点击刷新
            controller.post_click(*self.REFRESH_BUTTON).wait()
            time.sleep(0.5)
            
            # 点击确认
            controller.post_click(*self.CONFIRM_BUTTON).wait()
            time.sleep(1.0)
            
            return True


    @custom_action("FGO_SelectEnemy")
    class FGOSelectEnemyAction(CustomAction):
        """
        选择攻击目标
        
        参数:
            target: 目标位置 (0-5)
        """
        
        # 敌人位置
        ENEMY_POSITIONS = [
            (150, 100),   # 敌人1
            (400, 100),   # 敌人2
            (650, 100),   # 敌人3
            (250, 50),    # 后排敌人1
            (400, 50),    # 后排敌人2
            (550, 50),    # 后排敌人3
        ]

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            params = argv.custom_action_param or {}
            
            target = params.get("target", 0)
            
            if 0 <= target < len(self.ENEMY_POSITIONS):
                pos = self.ENEMY_POSITIONS[target]
                controller.post_click(*pos).wait()
                time.sleep(0.5)
            
            return True


    @custom_action("FGO_ClickScreen")
    class FGOClickScreenAction(CustomAction):
        """
        点击屏幕（用于跳过动画等）
        
        参数:
            times: 点击次数
            interval: 点击间隔（秒）
        """
        
        CLICK_POS = (640, 400)

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            params = argv.custom_action_param or {}
            
            times = params.get("times", 1)
            interval = params.get("interval", 0.3)
            
            for _ in range(times):
                controller.post_click(*self.CLICK_POS).wait()
                time.sleep(interval)
            
            return True


    @custom_action("FGO_WaitSeconds")
    class FGOWaitSecondsAction(CustomAction):
        """
        等待指定秒数
        
        参数:
            seconds: 等待秒数
        """

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            params = argv.custom_action_param or {}
            seconds = params.get("seconds", 1)
            time.sleep(seconds)
            return True


# 导出的动作列表
UTILITY_ACTIONS = [
    "FGO_LotteryRoll",
    "FGO_SelectSynthesisCards",
    "FGO_ScrollFriendList",
    "FGO_RefreshFriendList",
    "FGO_SelectEnemy",
    "FGO_ClickScreen",
    "FGO_WaitSeconds",
]

if __name__ == "__main__":
    print("Utility Actions:")
    for action in UTILITY_ACTIONS:
        print(f"  - {action}")
