"""
FGO 刷本相关的自定义动作
迁移自 fgoKernel.Main/Battle/Operation
"""

import time
from typing import Optional, Dict, Any

try:
    from maa.custom_action import CustomAction
    from maa.context import Context
    MAA_AVAILABLE = True
except ImportError:
    MAA_AVAILABLE = False

# 使用统一的 Resource 管理器
from .resource_manager import custom_action

if MAA_AVAILABLE:

    @custom_action("FGO_EatApple")
    class FGOEatAppleAction(CustomAction):
        """
        吃苹果恢复 AP
        
        参数:
            apple_kind: 苹果种类 (0=金苹果, 1=银苹果, 2=铜苹果, 3=彩虹苹果)
            cancel_if_empty: 如果没有苹果是否取消
        """
        
        # 苹果选择按钮位置
        APPLE_BUTTONS = {
            0: (640, 300),   # 金苹果
            1: (640, 400),   # 银苹果
            2: (640, 500),   # 铜苹果
            3: (640, 200),   # 彩虹苹果 (需要先滑动)
        }
        
        # 确认按钮
        CONFIRM_BUTTON = (900, 600)
        # 取消按钮
        CANCEL_BUTTON = (380, 600)

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            params = argv.custom_action_param or {}
            
            apple_kind = params.get("apple_kind", 0)
            cancel_if_empty = params.get("cancel_if_empty", True)
            
            if cancel_if_empty:
                # 点击取消
                controller.post_click(*self.CANCEL_BUTTON).wait()
                return True
            
            # 如果是彩虹苹果，需要先滑动
            if apple_kind == 3:
                controller.post_swipe(640, 400, 640, 200, 500).wait()
                time.sleep(0.6)
            
            # 点击苹果
            controller.post_click(*self.APPLE_BUTTONS[apple_kind]).wait()
            time.sleep(0.6)
            
            # 点击确认
            controller.post_click(*self.CONFIRM_BUTTON).wait()
            time.sleep(1.2)
            
            return True


    @custom_action("FGO_ChooseFriend")
    class FGOChooseFriendAction(CustomAction):
        """
        选择好友
        
        参数:
            friend_index: 好友索引 (0=第一个)
            scroll_to_find: 是否滚动查找
        """
        
        # 好友位置列表（第一页）
        FRIEND_POSITIONS = [
            (640, 280),   # 好友1
            (640, 430),   # 好友2
            (640, 580),   # 好友3
        ]

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            params = argv.custom_action_param or {}
            
            friend_index = params.get("friend_index", 0)
            
            # 简单实现：点击第一个好友
            if friend_index < len(self.FRIEND_POSITIONS):
                pos = self.FRIEND_POSITIONS[friend_index]
            else:
                pos = self.FRIEND_POSITIONS[0]
            
            controller.post_click(*pos).wait()
            time.sleep(1.0)
            
            return True


    @custom_action("FGO_BattleFormation")
    class FGOBattleFormationAction(CustomAction):
        """
        编队界面处理
        
        参数:
            team_index: 队伍索引 (0=不切换, 1-10=切换到指定队伍)
            auto_formation: 是否自动编队
        """
        
        # 队伍切换按钮 (F1-F10 对应的位置)
        TEAM_BUTTONS = [
            (100 + i * 65, 48) for i in range(10)
        ]
        
        # 开始战斗按钮
        START_BUTTON = (1180, 670)
        
        # 自动编队按钮
        AUTO_FORMATION_BUTTON = (100, 670)
        
        # 确认编队按钮
        CONFIRM_FORMATION = (900, 550)

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            params = argv.custom_action_param or {}
            
            team_index = params.get("team_index", 0)
            auto_formation = params.get("auto_formation", False)
            
            # 切换队伍
            if team_index > 0 and team_index <= 10:
                pos = self.TEAM_BUTTONS[team_index - 1]
                controller.post_click(*pos).wait()
                time.sleep(1.0)
            
            # 自动编队
            if auto_formation:
                controller.post_click(*self.AUTO_FORMATION_BUTTON).wait()
                time.sleep(1.5)
                controller.post_click(*self.CONFIRM_FORMATION).wait()
                time.sleep(2.0)
            
            # 点击开始战斗
            controller.post_click(*self.START_BUTTON).wait()
            time.sleep(2.5)
            
            return True


    @custom_action("FGO_ExecuteTurn")
    class FGOExecuteTurnAction(CustomAction):
        """
        执行战斗回合
        
        完整的回合执行，包括：
        1. 技能释放（如果配置）
        2. 点击 Attack
        3. 智能选卡（使用 CardSelector 算法）
        
        参数:
            skills: 技能配置列表 [{"servant": 0, "skill": 0, "target": null}, ...]
            use_hougu: 宝具使用配置 [false, false, false]
            smart_card: 是否使用智能选卡（默认 true）
        """
        
        ATTACK_BUTTON = (1180, 660)
        
        CARD_POSITIONS = [
            (128, 500), (385, 500), (642, 500), (899, 500), (1156, 500)
        ]
        
        HOUGU_POSITIONS = [
            (318, 250), (640, 250), (962, 250)
        ]
        
        SKILL_POSITIONS = [
            [(88, 592), (176, 592), (264, 592)],
            [(406, 592), (494, 592), (582, 592)],
            [(724, 592), (812, 592), (900, 592)],
        ]
        
        TARGET_POSITIONS = [
            (318, 400), (640, 400), (962, 400)
        ]
        
        # 敌人目标位置
        ENEMY_POSITIONS = [
            (150, 100), (400, 100), (650, 100),  # 前排
            (250, 50), (400, 50), (550, 50),      # 后排
        ]

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            from .battle_logic import CardSelector, get_battle_state
            import logging
            logger = logging.getLogger(__name__)
            
            controller = context.tasker.controller
            params = argv.custom_action_param or {}
            
            skills = params.get("skills", [])
            use_hougu = params.get("use_hougu", [False, False, False])
            smart_card = params.get("smart_card", True)
            select_target = params.get("select_target", True)
            
            # 释放技能
            for skill_config in skills:
                servant = skill_config.get("servant", 0)
                skill = skill_config.get("skill", 0)
                target = skill_config.get("target")
                
                # 点击技能
                pos = self.SKILL_POSITIONS[servant][skill]
                controller.post_click(*pos).wait()
                time.sleep(0.8)
                
                # 选择目标
                if target is not None:
                    target_pos = self.TARGET_POSITIONS[target]
                    controller.post_click(*target_pos).wait()
                    time.sleep(0.5)
            
            # 点击 Attack
            controller.post_click(*self.ATTACK_BUTTON).wait()
            time.sleep(2.0)
            
            # 计算宝具数量
            hougu_count = sum(1 for use in use_hougu if use)
            
            # 选择攻击目标（如果有宝具或需要选择目标）
            if select_target and (hougu_count > 0 or params.get("force_target", False)):
                # 选择血量最高的敌人
                battle_state = get_battle_state()
                target = battle_state.select_best_target()
                if target < len(self.ENEMY_POSITIONS):
                    controller.post_click(*self.ENEMY_POSITIONS[target]).wait()
                    time.sleep(0.5)
            
            # 点击宝具
            for i, use in enumerate(use_hougu):
                if use:
                    controller.post_click(*self.HOUGU_POSITIONS[i]).wait()
                    time.sleep(0.5)
            
            # 选择卡牌
            cards_to_select = 3 - hougu_count
            
            if cards_to_select > 0:
                if smart_card:
                    # 使用智能选卡算法
                    card_order = self._smart_select_cards(context, hougu_count)
                else:
                    # 简单按顺序选择
                    card_order = list(range(5))
                
                logger.info(f"Card selection order: {card_order[:cards_to_select]}")
                
                for i in range(cards_to_select):
                    card_idx = card_order[i]
                    controller.post_click(*self.CARD_POSITIONS[card_idx]).wait()
                    time.sleep(0.3)
            
            return True
        
        def _smart_select_cards(self, context: Context, hougu_count: int) -> list:
            """
            智能选卡：基于卡牌颜色、克制、暴击率计算最优组合
            """
            from .battle_logic import CardSelector
            import logging
            logger = logging.getLogger(__name__)
            
            try:
                # 尝试获取卡牌信息（需要检测适配器）
                # 这里使用默认值，实际应该从截图中识别
                
                # 默认参数（当无法识别时使用）
                color = [1.0, 1.0, 1.0, 1.0, 1.0]      # 默认绿卡
                resist = [1.0, 1.0, 1.0, 1.0, 1.0]     # 默认无克制
                critical = [0.0, 0.0, 0.0, 0.0, 0.0]   # 默认无暴击
                sealed = [False] * 5                   # 默认未封印
                group = [0, 0, 1, 1, 2]                # 默认从者分组
                
                # TODO: 从 context 获取卡牌检测结果
                # 可以通过 context.run_recognition 调用卡牌检测 Pipeline
                
                # 使用 CardSelector 选择最佳卡牌
                card_order = CardSelector.select_best_cards(
                    color=color,
                    resist=resist,
                    critical=critical,
                    sealed=sealed,
                    group=group,
                    hougu_count=hougu_count
                )
                
                return card_order
                
            except Exception as e:
                logger.warning(f"Smart card selection failed: {e}, using default order")
                return list(range(5))


    @custom_action("FGO_HandleDefeat")
    class FGOHandleDefeatAction(CustomAction):
        """
        处理战斗失败
        """
        
        # 放弃战斗按钮
        GIVE_UP_BUTTON = (460, 500)
        # 确认按钮
        CONFIRM_BUTTON = (640, 560)

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            
            # 点击放弃
            controller.post_click(*self.GIVE_UP_BUTTON).wait()
            time.sleep(0.5)
            
            # 点击确认
            controller.post_click(*self.CONFIRM_BUTTON).wait()
            time.sleep(0.5)
            
            # 再次确认
            controller.post_click(*self.CONFIRM_BUTTON).wait()
            time.sleep(0.5)
            
            return True


    @custom_action("FGO_SkipStory")
    class FGOSkipStoryAction(CustomAction):
        """
        跳过剧情
        """
        
        # 跳过按钮（右上角）
        SKIP_BUTTON = (1189, 44)
        # 确认跳过
        CONFIRM_SKIP = (825, 557)

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            
            # 点击跳过按钮
            controller.post_click(*self.SKIP_BUTTON).wait()
            time.sleep(0.8)
            
            # 点击确认
            controller.post_click(*self.CONFIRM_SKIP).wait()
            time.sleep(1.0)
            
            return True


# 导出的动作列表
FARMING_ACTIONS = [
    "FGO_EatApple",
    "FGO_ChooseFriend",
    "FGO_BattleFormation",
    "FGO_ExecuteTurn",
    "FGO_HandleDefeat",
    "FGO_SkipStory",
]

if __name__ == "__main__":
    print("Farming Actions:")
    for action in FARMING_ACTIONS:
        print(f"  - {action}")
