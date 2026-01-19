"""
FGO 战斗逻辑模块

包含完整的战斗决策系统：
- 卡牌颜色/克制检测
- 暴击率识别
- 智能选卡算法
- 技能释放决策

迁移自 fgoKernel.ClassicTurn 和 fgoKernel.Turn
"""

import logging
import numpy as np
from itertools import permutations
from typing import List, Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)


class CardSelector:
    """
    卡牌选择器 - 智能选卡算法
    
    移植自 fgoKernel.ClassicTurn 的选卡逻辑，
    计算最优卡牌组合以最大化伤害输出。
    """
    
    # 卡牌颜色系数: Arts=0.8, Quick=1.0, Buster=1.1
    COLOR_COEFFICIENTS = {
        0: 0.8,   # Arts (蓝卡)
        1: 1.0,   # Quick (绿卡)
        2: 1.1,   # Buster (红卡)
    }
    
    # 克制系数: 正常=1.0, 克制=1.7, 被克=0.6
    RESIST_COEFFICIENTS = {
        0: 1.0,   # 正常
        1: 1.7,   # 克制
        2: 0.6,   # 被克
    }
    
    @staticmethod
    def get_color_coefficient(color_type: int) -> float:
        """获取卡牌颜色系数"""
        return CardSelector.COLOR_COEFFICIENTS.get(color_type, 1.0)
    
    @staticmethod
    def get_resist_coefficient(resist_type: int) -> float:
        """获取克制系数"""
        return CardSelector.RESIST_COEFFICIENTS.get(resist_type, 1.0)
    
    @classmethod
    def evaluate_combo(
        cls,
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
            color: 各卡牌的颜色系数 [0.8/1.0/1.1]
            resist: 各卡牌的克制系数 [1.0/1.7/0.6]
            critical: 各卡牌的暴击率 (0.0-1.0)
            sealed: 各卡牌是否被封印
            group: 各卡牌所属从者索引
        
        Returns:
            伤害评分（越高越好）
        """
        # 检查是否有被封印的卡牌
        chain_error = any(sealed[i] for i in cards if i < len(sealed))
        
        # 颜色链检测（三张卡牌颜色相同）
        card_colors = [color[i] for i in cards if i < len(color)]
        color_chain = len(set(card_colors)) == 1 if card_colors else False
        
        # 首卡加成（红卡首位加 0.3）
        first_card_bonus = 0.3 if cards and cards[0] < len(color) and color[cards[0]] == 1.1 else 0
        
        # 位置系数
        pos_bonus = [1.0, 1.2, 1.4]
        
        # 计算基础伤害
        base_damage = 0.0
        for i, card_idx in enumerate(cards):
            if card_idx >= len(color):
                continue
            
            card_color = color[card_idx]
            card_resist = resist[card_idx] if card_idx < len(resist) else 1.0
            card_critical = critical[card_idx] if card_idx < len(critical) else 0.0
            card_sealed = sealed[card_idx] if card_idx < len(sealed) else False
            
            if not card_sealed:
                damage = (first_card_bonus + pos_bonus[i] * card_color) * \
                         (1 + card_critical) * card_resist
                base_damage += damage
        
        # 链加成
        chain_bonus = 0.0
        if not chain_error:
            # 同色链加成
            if color_chain:
                chain_bonus = 4.8  # 红链/蓝链/绿链额外伤害
            
            # 同从者链加成（Brave Chain）
            card_groups = [group[i] for i in cards if i < len(group)]
            same_servant = len(set(card_groups)) == 1 if card_groups else False
            if same_servant and cards[0] < len(resist):
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
        group: List[int],
        hougu_available: Optional[List[bool]] = None,
        hougu_count: int = 0
    ) -> List[int]:
        """
        选择最佳卡牌组合
        
        Args:
            color: 各卡牌的颜色系数
            resist: 各卡牌的克制系数
            critical: 各卡牌的暴击率
            sealed: 各卡牌是否被封印
            group: 各卡牌所属从者
            hougu_available: 各从者宝具是否可用 [bool, bool, bool]
            hougu_count: 本回合要使用的宝具数量
        
        Returns:
            5张卡牌的选择顺序 (0-4)，前3张为选中的卡牌
        """
        cards_to_select = 3 - hougu_count
        
        if cards_to_select <= 0:
            # 宝具占满了，不需要选普通卡
            return list(range(5))
        
        # 计算所有卡牌组合的评分
        all_combos = []
        for combo in permutations(range(5), cards_to_select):
            score = cls.evaluate_combo(combo, color, resist, critical, sealed, group)
            all_combos.append((combo, score))
        
        # 按评分降序排序
        all_combos.sort(key=lambda x: -x[1])
        
        # 记录调试日志
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Card ranking:")
            for i, (combo, score) in enumerate(all_combos[:10]):
                logger.debug(f"  {i+1}. {combo} -> {score:.2f}")
        
        # 选择最佳组合
        best_combo = list(all_combos[0][0])
        
        # 补全剩余卡牌
        remaining = [i for i in range(5) if i not in best_combo]
        
        # 按伤害排序剩余卡牌
        remaining.sort(key=lambda x: -color[x] * resist[x] * (not sealed[x]) * (1 + critical[x]))
        
        return best_combo + remaining


class BattleState:
    """
    战斗状态管理
    
    跟踪当前战斗的状态信息：
    - 当前关卡阶段
    - 从者状态
    - 技能冷却
    - 敌人信息
    """
    
    def __init__(self):
        self.stage = 1
        self.stage_total = 3
        self.stage_turn = 1
        self.turn = 0
        
        # 从者状态 [位置0, 位置1, 位置2]
        self.servant_alive = [True, True, True]
        self.servant_np = [0, 0, 0]
        self.servant_hp = [0, 0, 0]
        
        # 技能冷却 [从者][技能] = 剩余回合
        self.skill_cooldown = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        
        # 御主技能冷却
        self.master_skill_cooldown = [0, 0, 0]
        
        # 敌人信息
        self.enemy_hp = [0] * 6
        self.current_target = 0
    
    def new_turn(self, current_stage: int, stage_total: int):
        """新回合开始"""
        self.turn += 1
        
        # 检测阶段变化
        if current_stage != self.stage:
            self.stage = current_stage
            self.stage_turn = 1
        else:
            self.stage_turn += 1
        
        self.stage_total = stage_total
        
        # 减少技能冷却
        for i in range(3):
            for j in range(3):
                self.skill_cooldown[i][j] = max(0, self.skill_cooldown[i][j] - 1)
        
        for i in range(3):
            self.master_skill_cooldown[i] = max(0, self.master_skill_cooldown[i] - 1)
    
    def use_skill(self, servant: int, skill: int, cooldown: int = 5):
        """使用从者技能"""
        self.skill_cooldown[servant][skill] = cooldown
    
    def use_master_skill(self, skill: int, cooldown: int = 15):
        """使用御主技能"""
        self.master_skill_cooldown[skill] = cooldown
    
    def is_skill_ready(self, servant: int, skill: int) -> bool:
        """检查从者技能是否可用"""
        return self.skill_cooldown[servant][skill] == 0
    
    def is_master_skill_ready(self, skill: int) -> bool:
        """检查御主技能是否可用"""
        return self.master_skill_cooldown[skill] == 0
    
    def update_enemy_hp(self, hp_list: List[int]):
        """更新敌人血量"""
        for i, hp in enumerate(hp_list):
            if i < len(self.enemy_hp):
                self.enemy_hp[i] = hp
    
    def select_best_target(self) -> int:
        """选择最佳攻击目标（血量最高的敌人）"""
        max_hp = 0
        best_target = 0
        for i, hp in enumerate(self.enemy_hp):
            if hp > max_hp:
                max_hp = hp
                best_target = i
        return best_target


# 全局战斗状态
_battle_state: Optional[BattleState] = None


def get_battle_state() -> BattleState:
    """获取全局战斗状态"""
    global _battle_state
    if _battle_state is None:
        _battle_state = BattleState()
    return _battle_state


def reset_battle_state():
    """重置战斗状态（新战斗开始时调用）"""
    global _battle_state
    _battle_state = BattleState()
