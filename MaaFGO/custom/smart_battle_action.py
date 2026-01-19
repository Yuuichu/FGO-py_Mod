"""
FGO 智能战斗动作

完整的智能战斗系统，包含：
- 自动技能释放（基于冷却和条件）
- 敌人血量追踪和目标选择
- 智能选卡
- 宝具判断

迁移自 fgoKernel.Turn
"""

import time
import logging
from typing import List, Dict, Any, Optional

try:
    from maa.custom_action import CustomAction
    from maa.context import Context
    MAA_AVAILABLE = True
except ImportError:
    MAA_AVAILABLE = False

from .resource_manager import custom_action
from .battle_logic import CardSelector, BattleState, get_battle_state, reset_battle_state

logger = logging.getLogger(__name__)


# 坐标常量（基于 720p）
class Positions:
    """战斗界面坐标定义"""
    
    # Attack 按钮
    ATTACK = (1180, 660)
    
    # 卡牌位置 (5张)
    CARDS = [
        (128, 500), (385, 500), (642, 500), (899, 500), (1156, 500)
    ]
    
    # 宝具位置 (3个)
    HOUGU = [
        (318, 250), (640, 250), (962, 250)
    ]
    
    # 从者技能位置 [从者][技能]
    SKILLS = [
        [(88, 592), (176, 592), (264, 592)],    # 从者1
        [(406, 592), (494, 592), (582, 592)],   # 从者2
        [(724, 592), (812, 592), (900, 592)],   # 从者3
    ]
    
    # 技能目标位置
    SKILL_TARGETS = [
        (318, 400), (640, 400), (962, 400)
    ]
    
    # 御主技能按钮
    MASTER_BUTTON = (1200, 340)
    
    # 御主技能位置
    MASTER_SKILLS = [
        (1000, 430), (1100, 430), (1200, 430)
    ]
    
    # 换人目标位置
    ORDER_CHANGE_FRONT = [(200, 360), (400, 360), (600, 360)]
    ORDER_CHANGE_BACK = [(800, 360), (1000, 360), (1100, 360)]
    ORDER_CHANGE_CONFIRM = (640, 550)
    
    # 敌人位置
    ENEMIES = [
        (150, 100), (400, 100), (650, 100),  # 前排
        (250, 50), (400, 50), (550, 50),      # 后排
    ]


if MAA_AVAILABLE:

    @custom_action("FGO_SmartBattle")
    class FGOSmartBattleAction(CustomAction):
        """
        FGO 智能战斗动作
        
        自动执行一个完整的战斗回合，包括：
        - 检测并释放可用技能
        - 检测敌人血量选择目标
        - 智能选择卡牌组合
        - 判断是否使用宝具
        
        参数:
            auto_skill: 是否自动释放技能（默认 false）
            skill_config: 技能配置 {"servant_skills": [[1,1,1],[1,1,1],[1,1,1]], "master_skills": [0,0,0]}
            hougu_threshold: 宝具使用阈值（敌人血量大于此值时使用）
            smart_card: 是否使用智能选卡（默认 true）
        """

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            params = argv.custom_action_param or {}
            
            auto_skill = params.get("auto_skill", False)
            skill_config = params.get("skill_config", {})
            hougu_threshold = params.get("hougu_threshold", 50000)
            smart_card = params.get("smart_card", True)
            
            battle_state = get_battle_state()
            
            try:
                # 1. 检测敌人血量
                enemy_hp = self._detect_enemy_hp(context)
                battle_state.update_enemy_hp(enemy_hp)
                logger.info(f"Enemy HP: {enemy_hp}")
                
                # 2. 检测关卡阶段
                stage, stage_total = self._detect_stage(context)
                battle_state.new_turn(stage, stage_total)
                logger.info(f"Turn {battle_state.turn}, Stage {stage}/{stage_total}")
                
                # 3. 自动释放技能
                if auto_skill:
                    self._auto_cast_skills(context, controller, battle_state, skill_config)
                
                # 4. 点击 Attack
                controller.post_click(*Positions.ATTACK).wait()
                time.sleep(2.0)
                
                # 5. 判断宝具使用
                use_hougu = self._decide_hougu(context, battle_state, hougu_threshold)
                hougu_count = sum(1 for use in use_hougu if use)
                
                # 6. 选择目标
                if hougu_count > 0 or battle_state.stage_turn == 1:
                    target = battle_state.select_best_target()
                    if target < len(Positions.ENEMIES):
                        controller.post_click(*Positions.ENEMIES[target]).wait()
                        time.sleep(0.5)
                
                # 7. 点击宝具
                for i, use in enumerate(use_hougu):
                    if use:
                        controller.post_click(*Positions.HOUGU[i]).wait()
                        time.sleep(0.5)
                
                # 8. 选择卡牌
                cards_to_select = 3 - hougu_count
                if cards_to_select > 0:
                    card_order = self._select_cards(context, smart_card, hougu_count)
                    for i in range(cards_to_select):
                        controller.post_click(*Positions.CARDS[card_order[i]]).wait()
                        time.sleep(0.3)
                
                return True
                
            except Exception as e:
                logger.error(f"Smart battle action failed: {e}")
                # 降级到简单执行
                return self._fallback_turn(controller)
        
        def _detect_enemy_hp(self, context: Context) -> List[int]:
            """检测敌人血量"""
            # TODO: 使用 OCR 检测敌人血量
            # 暂时返回默认值
            return [10000, 10000, 10000, 0, 0, 0]
        
        def _detect_stage(self, context: Context) -> tuple:
            """检测关卡阶段"""
            # TODO: 使用 OCR 检测阶段
            return (1, 3)
        
        def _auto_cast_skills(
            self, 
            context: Context, 
            controller, 
            battle_state: BattleState,
            skill_config: dict
        ):
            """自动释放技能"""
            servant_skills = skill_config.get("servant_skills", [[0,0,0],[0,0,0],[0,0,0]])
            
            for servant in range(3):
                for skill in range(3):
                    # 检查技能是否配置为自动释放
                    if servant_skills[servant][skill] == 0:
                        continue
                    
                    # 检查冷却
                    if not battle_state.is_skill_ready(servant, skill):
                        continue
                    
                    # 释放技能
                    logger.info(f"Casting skill: servant={servant}, skill={skill}")
                    controller.post_click(*Positions.SKILLS[servant][skill]).wait()
                    time.sleep(0.8)
                    
                    # 如果需要选择目标
                    target = servant_skills[servant][skill]
                    if target > 0 and target <= 3:
                        controller.post_click(*Positions.SKILL_TARGETS[target - 1]).wait()
                        time.sleep(0.5)
                    
                    # 记录冷却
                    battle_state.use_skill(servant, skill)
                    
                    # 等待技能动画
                    time.sleep(1.0)
        
        def _decide_hougu(
            self, 
            context: Context, 
            battle_state: BattleState,
            threshold: int
        ) -> List[bool]:
            """判断是否使用宝具"""
            use_hougu = [False, False, False]
            
            # 检测 NP 是否满
            # TODO: 使用检测器判断宝具是否可用
            
            # 最后一面时使用所有可用宝具
            if battle_state.stage == battle_state.stage_total:
                # 假设所有宝具都可用（需要实际检测）
                return [True, True, True]
            
            # 根据敌人血量判断
            max_enemy_hp = max(battle_state.enemy_hp) if battle_state.enemy_hp else 0
            if max_enemy_hp > threshold:
                # 使用第一个可用的宝具
                use_hougu[0] = True
            
            return use_hougu
        
        def _select_cards(self, context: Context, smart: bool, hougu_count: int) -> List[int]:
            """选择卡牌"""
            if not smart:
                return list(range(5))
            
            # 使用 CardSelector
            # 默认参数（需要实际检测）
            return CardSelector.select_best_cards(
                color=[1.0] * 5,
                resist=[1.0] * 5,
                critical=[0.0] * 5,
                sealed=[False] * 5,
                group=[0, 0, 1, 1, 2],
                hougu_count=hougu_count
            )
        
        def _fallback_turn(self, controller) -> bool:
            """降级执行：简单点击"""
            try:
                controller.post_click(*Positions.ATTACK).wait()
                time.sleep(2.0)
                
                for i in range(3):
                    controller.post_click(*Positions.CARDS[i]).wait()
                    time.sleep(0.3)
                
                return True
            except Exception as e:
                logger.error(f"Fallback turn failed: {e}")
                return False


    @custom_action("FGO_CastServantSkill")
    class FGOCastServantSkillAction(CustomAction):
        """
        释放从者技能（带冷却追踪）
        
        参数:
            servant: 从者位置 (0-2)
            skill: 技能位置 (0-2)
            target: 目标位置 (0-2, 可选)
            cooldown: 技能冷却回合数（默认 5）
        """

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            params = argv.custom_action_param or {}
            
            servant = params.get("servant", 0)
            skill = params.get("skill", 0)
            target = params.get("target")
            cooldown = params.get("cooldown", 5)
            
            battle_state = get_battle_state()
            
            # 检查冷却
            if not battle_state.is_skill_ready(servant, skill):
                logger.warning(f"Skill {servant}-{skill} is on cooldown")
                return False
            
            # 点击技能
            controller.post_click(*Positions.SKILLS[servant][skill]).wait()
            time.sleep(0.8)
            
            # 选择目标
            if target is not None and 0 <= target <= 2:
                controller.post_click(*Positions.SKILL_TARGETS[target]).wait()
                time.sleep(0.5)
            
            # 记录冷却
            battle_state.use_skill(servant, skill, cooldown)
            
            return True


    @custom_action("FGO_CastMasterSkillTracked")
    class FGOCastMasterSkillTrackedAction(CustomAction):
        """
        释放御主技能（带冷却追踪）
        
        参数:
            skill: 技能位置 (0-2)
            target1: 第一目标 (可选)
            target2: 第二目标 (换人用，可选)
        """

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            params = argv.custom_action_param or {}
            
            skill = params.get("skill", 0)
            target1 = params.get("target1")
            target2 = params.get("target2")
            
            battle_state = get_battle_state()
            
            # 检查冷却
            if not battle_state.is_master_skill_ready(skill):
                logger.warning(f"Master skill {skill} is on cooldown")
                return False
            
            # 打开御主技能菜单
            controller.post_click(*Positions.MASTER_BUTTON).wait()
            time.sleep(0.5)
            
            # 点击技能
            controller.post_click(*Positions.MASTER_SKILLS[skill]).wait()
            time.sleep(0.5)
            
            # 如果是换人技能（技能3）
            if skill == 2 and target1 is not None and target2 is not None:
                # 选择前排目标
                controller.post_click(*Positions.ORDER_CHANGE_FRONT[target1]).wait()
                time.sleep(0.3)
                # 选择后排目标
                controller.post_click(*Positions.ORDER_CHANGE_BACK[target2]).wait()
                time.sleep(0.3)
                # 确认
                controller.post_click(*Positions.ORDER_CHANGE_CONFIRM).wait()
                time.sleep(2.5)
            elif target1 is not None and 0 <= target1 <= 2:
                controller.post_click(*Positions.SKILL_TARGETS[target1]).wait()
                time.sleep(0.5)
            
            # 记录冷却
            battle_state.use_master_skill(skill)
            
            return True


    @custom_action("FGO_ResetBattleState")
    class FGOResetBattleStateAction(CustomAction):
        """
        重置战斗状态（新战斗开始时调用）
        """

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            reset_battle_state()
            logger.info("Battle state reset")
            return True


    @custom_action("FGO_SelectBestTarget")
    class FGOSelectBestTargetAction(CustomAction):
        """
        选择最佳攻击目标（血量最高的敌人）
        """

        def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
            controller = context.tasker.controller
            battle_state = get_battle_state()
            
            target = battle_state.select_best_target()
            
            if target < len(Positions.ENEMIES):
                controller.post_click(*Positions.ENEMIES[target]).wait()
                time.sleep(0.5)
                logger.info(f"Selected target: {target}")
                return True
            
            return False
