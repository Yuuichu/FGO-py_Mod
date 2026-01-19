"""
MaaFGO Custom Recognition/Action 模块

包含：
- resource_manager: 统一的 Resource 管理器
- battle_logic: 战斗逻辑和选卡算法
- fgo_actions: 基础战斗动作
- farming_actions: 刷本相关动作
- utility_actions: 实用功能动作
- smart_battle_action: 智能战斗动作
"""

# 首先导入 Resource 管理器
from . import resource_manager
from .resource_manager import (
    ResourceManager,
    get_resource,
    set_resource,
    custom_recognition,
    custom_action,
)

# 导入战斗逻辑
from . import battle_logic
from .battle_logic import (
    CardSelector,
    BattleState,
    get_battle_state,
    reset_battle_state,
)

# 导入所有自定义动作（会自动通过装饰器注册）
from . import fgo_actions
from . import farming_actions
from . import utility_actions
from . import smart_battle_action
from . import advanced_actions

# 导入高级功能
from .advanced_actions import (
    NetworkGuardian,
    FarmingStats,
    get_farming_stats,
    reset_farming_stats,
)

# 汇总所有可用的识别器和动作
ALL_RECOGNITIONS = ResourceManager.get_registered_recognitions()
ALL_ACTIONS = ResourceManager.get_registered_actions()

__all__ = [
    # 资源管理
    "resource_manager",
    "ResourceManager",
    "get_resource",
    "set_resource",
    "custom_recognition",
    "custom_action",
    # 战斗逻辑
    "battle_logic",
    "CardSelector",
    "BattleState",
    "get_battle_state",
    "reset_battle_state",
    # 高级功能
    "advanced_actions",
    "NetworkGuardian",
    "FarmingStats",
    "get_farming_stats",
    "reset_farming_stats",
    # 模块
    "fgo_actions",
    "farming_actions", 
    "utility_actions",
    "smart_battle_action",
    # 列表
    "ALL_RECOGNITIONS",
    "ALL_ACTIONS",
]
