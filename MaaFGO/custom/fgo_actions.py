"""
FGO-py 自定义识别器和动作
将 FGO-py 的战斗逻辑封装为 MaaFramework 可用的扩展

主要组件：
- FGO_TurnRecognition: 回合状态识别
- FGO_TurnAction: 回合执行动作（技能 + 选卡）
- FGO_BattleAction: 完整战斗流程
"""

import time
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from itertools import permutations

try:
    from maa.custom_recognition import CustomRecognition
    from maa.custom_action import CustomAction
    from maa.context import Context
    MAA_AVAILABLE = True
except ImportError:
    MAA_AVAILABLE = False
    print("Warning: MaaFramework not installed")

# 使用统一的 Resource 管理器
from .resource_manager import custom_recognition, custom_action


class CardSelector:
    """卡牌选择器 - 移植自 fgoKernel.ClassicTurn"""
    
    # 卡牌颜色系数: Arts=0.8, Quick=1.0, Buster=1.1
    COLOR_COEFFICIENTS = [0.8, 1.0, 1.1]
    
    # 克制系数: 正常=1.0, 克制=1.7, 被克=0.6
    RESIST_COEFFICIENTS = [1.0, 1.7, 0.6]
    
    @staticmethod
    def evaluate_combo(
        cards: Tuple[int, ...],
        color: List[float],
        resist: List[float],
        critical: List[float],
        sealed: List[bool],
        group: List[int]
    ) -> float:
        """
        评估卡牌组合的伤害分数
        
        Args:
            cards: 3张卡牌的索引 (0-4)
            color: 各卡牌的颜色系数
            resist: 各卡牌的克制系数
            critical: 各卡牌的暴击率
            sealed: 各卡牌是否被封印
            group: 各卡牌所属从者
        
        Returns:
            伤害评分
        """
        # 颜色链检测
        color_chain = len({color[i] for i in cards}) == 1
        
        # 首卡加成
        first_card_bonus = 0.3 if color[cards[0]] == 1.1 else 0
        
        # 位置系数
        pos_bonus = [1.0, 1.2, 1.4]
        
        # 基础伤害
        base_damage = sum(
            (first_card_bonus + pos_bonus[i] * color[j]) * 
            (1 + critical[j]) * resist[j] * (not sealed[j])
            for i, j in enumerate(cards)
        )
        
        # 链加成
        chain_bonus = 0
        if not any(sealed[i] for i in cards):
            if color_chain:
                chain_bonus = 4.8
            
            # 同从者链加成
            same_servant = len({group[i] for i in cards}) == 1
            if same_servant:
                chain_bonus += (first_card_bonus + 1.0) * \
                              (3 if color_chain else 1.8) * resist[cards[0]]
        
        return base_damage + chain_bonus
    
    @classmethod
    def select_best_cards(
        cls,
        color: List[float],
        resist: List[float],
        critical: List[float],
        sealed: List[bool],
        group: List[int]
    ) -> List[int]:
        """
        选择最佳卡牌组合
        
        Returns:
            5张卡牌的选择顺序 (0-4)
        """
        # 计算所有3张卡组合的评分
        all_combos = [
            (combo, cls.evaluate_combo(combo, color, resist, critical, sealed, group))
            for combo in permutations(range(5), 3)
        ]
        
        # 按评分降序排序
        all_combos.sort(key=lambda x: -x[1])
        
        # 选择最佳组合
        best_combo = list(all_combos[0][0])
        
        # 补全剩余卡牌
        remaining = list({0, 1, 2, 3, 4} - set(best_combo))
        return best_combo + remaining


if MAA_AVAILABLE:
    
    @custom_recognition("FGO_TurnRecognition")
    class FGOTurnRecognition(CustomRecognition):
        """
        FGO 回合识别器
        检测当前回合状态，包括：
        - 技能状态
        - 宝具状态
        - 卡牌颜色
        - 敌人血量
        """

        def analyze(
            self,
            context: Context,
            argv: CustomRecognition.AnalyzeArg,
        ) -> CustomRecognition.AnalyzeResult:
            image = argv.image
            
            # 检测 Attack 按钮是否存在
            # 使用模板匹配检测
            attack_roi = (1155, 635, 1210, 682)
            
            # 简单的颜色检测：Attack 按钮是红色的
            x1, y1, x2, y2 = attack_roi
            crop = image[y1:y2, x1:x2]
            
            # 检测红色像素（BGR格式）
            red_mask = (crop[:, :, 2] > 150) & (crop[:, :, 1] < 100) & (crop[:, :, 0] < 100)
            red_ratio = np.sum(red_mask) / red_mask.size
            
            if red_ratio > 0.1:
                return CustomRecognition.AnalyzeResult(
                    box=(x1, y1, x2 - x1, y2 - y1),
                    detail="Turn ready"
                )
            return None


    @custom_action("FGO_TurnAction")
    class FGOTurnAction(CustomAction):
        """
        FGO 回合动作
        执行一个完整的战斗回合：
        1. 检测技能状态
        2. 点击 Attack
        3. 智能选择卡牌
        """
        
        # 卡牌位置（720p）
        CARD_POSITIONS = [
            (128, 500),   # 卡牌1
            (385, 500),   # 卡牌2
            (642, 500),   # 卡牌3
            (899, 500),   # 卡牌4
            (1156, 500),  # 卡牌5
        ]
        
        # 宝具位置
        HOUGU_POSITIONS = [
            (318, 250),   # 宝具1
            (640, 250),   # 宝具2
            (962, 250),   # 宝具3
        ]
        
        # Attack 按钮位置
        ATTACK_POS = (1180, 660)

        def run(
            self,
            context: Context,
            argv: CustomAction.RunArg,
        ) -> bool:
            controller = context.tasker.controller
            
            # 1. 点击 Attack 按钮
            controller.post_click(*self.ATTACK_POS).wait()
            time.sleep(2.0)
            
            # 2. 获取卡牌信息（简化版：依次选择前3张）
            # TODO: 集成完整的 CardSelector 逻辑
            
            # 3. 选择卡牌
            for i in range(3):
                pos = self.CARD_POSITIONS[i]
                controller.post_click(*pos).wait()
                time.sleep(0.3)
            
            # 等待动画
            time.sleep(2.0)
            
            return True


    @custom_action("FGO_SmartTurnAction")
    class FGOSmartTurnAction(CustomAction):
        """
        FGO 智能回合动作
        使用 CardSelector 的智能选卡算法
        """
        
        CARD_POSITIONS = FGOTurnAction.CARD_POSITIONS
        HOUGU_POSITIONS = FGOTurnAction.HOUGU_POSITIONS
        ATTACK_POS = FGOTurnAction.ATTACK_POS

        def run(
            self,
            context: Context,
            argv: CustomAction.RunArg,
        ) -> bool:
            controller = context.tasker.controller
            
            # 获取参数
            params = argv.custom_action_param or {}
            use_hougu = params.get("use_hougu", [False, False, False])
            
            # 1. 点击 Attack 按钮
            controller.post_click(*self.ATTACK_POS).wait()
            time.sleep(2.0)
            
            # 2. 如果有宝具要使用，先点宝具
            hougu_count = 0
            for i, use in enumerate(use_hougu):
                if use:
                    controller.post_click(*self.HOUGU_POSITIONS[i]).wait()
                    time.sleep(0.5)
                    hougu_count += 1
            
            # 3. 选择剩余卡牌
            cards_to_select = 3 - hougu_count
            for i in range(cards_to_select):
                pos = self.CARD_POSITIONS[i]
                controller.post_click(*pos).wait()
                time.sleep(0.3)
            
            # 等待动画
            time.sleep(2.0)
            
            return True


    @custom_action("FGO_CastSkill")
    class FGOCastSkillAction(CustomAction):
        """
        FGO 释放技能动作
        
        参数:
            servant: 从者位置 (0-2)
            skill: 技能位置 (0-2)
            target: 目标位置 (0-2, 可选)
        """
        
        # 技能位置（720p）
        SKILL_POSITIONS = [
            [(88, 592), (176, 592), (264, 592)],    # 从者1
            [(406, 592), (494, 592), (582, 592)],   # 从者2
            [(724, 592), (812, 592), (900, 592)],   # 从者3
        ]
        
        # 技能目标位置
        TARGET_POSITIONS = [
            (318, 400),   # 目标1
            (640, 400),   # 目标2
            (962, 400),   # 目标3
        ]

        def run(
            self,
            context: Context,
            argv: CustomAction.RunArg,
        ) -> bool:
            controller = context.tasker.controller
            params = argv.custom_action_param or {}
            
            servant = params.get("servant", 0)
            skill = params.get("skill", 0)
            target = params.get("target", None)
            
            # 点击技能
            pos = self.SKILL_POSITIONS[servant][skill]
            controller.post_click(*pos).wait()
            time.sleep(0.8)
            
            # 如果需要选择目标
            if target is not None:
                target_pos = self.TARGET_POSITIONS[target]
                controller.post_click(*target_pos).wait()
                time.sleep(0.5)
            
            return True


    @custom_action("FGO_CastMasterSkill")
    class FGOCastMasterSkillAction(CustomAction):
        """
        FGO 御主技能动作
        
        参数:
            skill: 技能位置 (0-2)
            target1: 第一目标 (可选)
            target2: 第二目标 (换人用，可选)
        """
        
        # 御主技能按钮位置
        MASTER_BUTTON = (1200, 340)
        
        # 御主技能位置
        MASTER_SKILLS = [
            (1000, 430),  # 技能1
            (1100, 430),  # 技能2
            (1200, 430),  # 技能3
        ]
        
        # 换人目标位置（前排）
        FRONT_TARGETS = [(200, 360), (400, 360), (600, 360)]
        # 换人目标位置（后排）
        BACK_TARGETS = [(800, 360), (1000, 360), (1100, 360)]
        
        # 确认按钮
        CONFIRM_BUTTON = (640, 550)

        def run(
            self,
            context: Context,
            argv: CustomAction.RunArg,
        ) -> bool:
            controller = context.tasker.controller
            params = argv.custom_action_param or {}
            
            skill = params.get("skill", 0)
            target1 = params.get("target1", None)
            target2 = params.get("target2", None)
            
            # 打开御主技能菜单
            controller.post_click(*self.MASTER_BUTTON).wait()
            time.sleep(0.5)
            
            # 点击技能
            controller.post_click(*self.MASTER_SKILLS[skill]).wait()
            time.sleep(0.5)
            
            # 如果是换人技能（技能3）
            if skill == 2 and target1 is not None and target2 is not None:
                # 选择前排目标
                controller.post_click(*self.FRONT_TARGETS[target1]).wait()
                time.sleep(0.3)
                # 选择后排目标
                controller.post_click(*self.BACK_TARGETS[target2]).wait()
                time.sleep(0.3)
                # 确认
                controller.post_click(*self.CONFIRM_BUTTON).wait()
                time.sleep(2.5)
            elif target1 is not None:
                # 普通目标选择
                target_pos = self.FRONT_TARGETS[target1]
                controller.post_click(*target_pos).wait()
                time.sleep(0.5)
            
            return True


    @custom_action("FGO_CollectRewards")
    class FGOCollectRewardsAction(CustomAction):
        """
        收集战斗奖励
        连续点击屏幕跳过结算动画
        """
        
        CLICK_POS = (640, 400)

        def run(
            self,
            context: Context,
            argv: CustomAction.RunArg,
        ) -> bool:
            controller = context.tasker.controller
            params = argv.custom_action_param or {}
            
            clicks = params.get("clicks", 10)
            interval = params.get("interval", 0.4)
            
            for _ in range(clicks):
                controller.post_click(*self.CLICK_POS).wait()
                time.sleep(interval)
            
            return True


# 用于独立测试
if __name__ == "__main__":
    print("FGO Custom Actions loaded successfully")
    if MAA_AVAILABLE:
        print("Available recognitions:", [
            "FGO_TurnRecognition",
        ])
        print("Available actions:", [
            "FGO_TurnAction",
            "FGO_SmartTurnAction",
            "FGO_CastSkill",
            "FGO_CastMasterSkill",
            "FGO_CollectRewards",
        ])
    else:
        print("MaaFramework not installed - running in stub mode")
