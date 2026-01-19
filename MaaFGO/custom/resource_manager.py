"""
MaaFGO Resource 管理器

统一管理 MaaFramework Resource 实例，确保所有自定义识别器和动作
都注册到同一个 Resource 对象中。
"""

from typing import Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)

try:
    from maa.resource import Resource
    from maa.custom_recognition import CustomRecognition
    from maa.custom_action import CustomAction
    MAA_AVAILABLE = True
except ImportError:
    MAA_AVAILABLE = False
    Resource = None
    CustomRecognition = None
    CustomAction = None
    logger.warning("MaaFramework not installed. Run: pip install MaaFw")


class ResourceManager:
    """
    全局 Resource 管理器
    
    使用单例模式确保整个应用中只有一个 Resource 实例。
    所有自定义识别器和动作都注册到这个实例上。
    """
    
    _instance: Optional['ResourceManager'] = None
    _resource: Optional['Resource'] = None
    _recognitions: dict = {}
    _actions: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'ResourceManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def get_resource(cls) -> Optional['Resource']:
        """获取 Resource 实例"""
        return cls._resource
    
    @classmethod
    def set_resource(cls, resource: 'Resource'):
        """
        设置 Resource 实例并注册所有已缓存的自定义组件
        
        Args:
            resource: MaaFramework Resource 实例
        """
        cls._resource = resource
        # 注册所有缓存的识别器
        for name, recognizer_class in cls._recognitions.items():
            try:
                resource.register(recognizer_class())
                logger.info(f"Registered recognition: {name}")
            except Exception as e:
                logger.error(f"Failed to register recognition {name}: {e}")
        
        # 注册所有缓存的动作
        for name, action_class in cls._actions.items():
            try:
                resource.register(action_class())
                logger.info(f"Registered action: {name}")
            except Exception as e:
                logger.error(f"Failed to register action {name}: {e}")
    
    @classmethod
    def register_recognition(cls, name: str):
        """
        装饰器：注册自定义识别器
        
        如果 Resource 已设置，立即注册；否则缓存等待后续注册。
        
        Args:
            name: 识别器名称
        """
        def decorator(recognizer_class):
            cls._recognitions[name] = recognizer_class
            
            # 如果 Resource 已经设置，立即注册
            if cls._resource is not None:
                try:
                    cls._resource.register(recognizer_class())
                    logger.info(f"Registered recognition: {name}")
                except Exception as e:
                    logger.error(f"Failed to register recognition {name}: {e}")
            
            return recognizer_class
        return decorator
    
    @classmethod
    def register_action(cls, name: str):
        """
        装饰器：注册自定义动作
        
        如果 Resource 已设置，立即注册；否则缓存等待后续注册。
        
        Args:
            name: 动作名称
        """
        def decorator(action_class):
            cls._actions[name] = action_class
            
            # 如果 Resource 已经设置，立即注册
            if cls._resource is not None:
                try:
                    cls._resource.register(action_class())
                    logger.info(f"Registered action: {name}")
                except Exception as e:
                    logger.error(f"Failed to register action {name}: {e}")
            
            return action_class
        return decorator
    
    @classmethod
    def get_registered_recognitions(cls) -> list:
        """获取所有已注册的识别器名称"""
        return list(cls._recognitions.keys())
    
    @classmethod
    def get_registered_actions(cls) -> list:
        """获取所有已注册的动作名称"""
        return list(cls._actions.keys())
    
    @classmethod
    def clear(cls):
        """清空所有注册信息（用于测试）"""
        cls._resource = None
        cls._recognitions.clear()
        cls._actions.clear()


# 便捷函数
def get_resource() -> Optional['Resource']:
    """获取全局 Resource 实例"""
    return ResourceManager.get_resource()


def set_resource(resource: 'Resource'):
    """设置全局 Resource 实例"""
    ResourceManager.set_resource(resource)


def custom_recognition(name: str):
    """装饰器：注册自定义识别器"""
    return ResourceManager.register_recognition(name)


def custom_action(name: str):
    """装饰器：注册自定义动作"""
    return ResourceManager.register_action(name)
