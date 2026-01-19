#!/usr/bin/env python3
"""
MaaFGO Runner - 使用 MaaFramework 运行 FGO 自动化

这是一个完整的示例，展示如何使用 MaaFramework 的 Tasker
来执行 FGO-py 的自动化任务。

使用方法：
    python run_with_maa.py                     # 默认连接
    python run_with_maa.py --task AutoFarming  # 指定任务
    python run_with_maa.py --debug             # 调试模式
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from maa.resource import Resource
    from maa.controller import AdbController
    from maa.tasker import Tasker
    from maa.toolkit import Toolkit
    MAA_AVAILABLE = True
except ImportError:
    MAA_AVAILABLE = False
    logger.error("MaaFramework not installed. Run: pip install MaaFw")
    sys.exit(1)


class MaaFGORunner:
    """MaaFGO 运行器"""
    
    def __init__(
        self,
        resource_path: Optional[Path] = None,
        debug: bool = False
    ):
        self.debug = debug
        self.resource_path = resource_path or Path(__file__).parent / "resource"
        
        self.resource: Optional[Resource] = None
        self.controller: Optional[AdbController] = None
        self.tasker: Optional[Tasker] = None
        
        # 初始化 Toolkit
        Toolkit.init_option(str(Path(__file__).parent))
    
    def connect(self, address: str = None) -> bool:
        """连接设备"""
        logger.info("Searching for devices...")
        
        devices = Toolkit.find_adb_devices()
        if not devices:
            logger.warning("No ADB devices found.")
            return False
        
        # 选择设备
        if address:
            device = next((d for d in devices if d.address == address), None)
            if not device:
                logger.error(f"Device not found: {address}")
                return False
        else:
            device = devices[0]
        
        logger.info(f"Connecting to: {device.name} ({device.address})")
        
        # 创建控制器
        self.controller = AdbController(
            adb_path=device.adb_path,
            address=device.address,
        )
        self.controller.set_screenshot_target_short_side(720)
        
        # 连接
        status = self.controller.post_connection().wait()
        if not status.succeeded():
            logger.error("Connection failed!")
            return False
        
        logger.info("Connected successfully!")
        return True
    
    def load_resources(self) -> bool:
        """加载资源"""
        logger.info(f"Loading resources from: {self.resource_path}")
        
        self.resource = Resource()
        
        # 加载主资源
        status = self.resource.post_bundle(str(self.resource_path)).wait()
        if not status.succeeded():
            logger.error("Failed to load resources!")
            return False
        
        # 注册自定义识别器和动作
        self._register_custom_components()
        
        logger.info("Resources loaded!")
        return True
    
    def _register_custom_components(self):
        """注册自定义组件到统一的 Resource 实例"""
        try:
            # 导入自定义模块
            sys.path.insert(0, str(Path(__file__).parent))
            
            # 使用统一的 ResourceManager
            from custom.resource_manager import ResourceManager
            
            # 设置全局 Resource 实例，这会自动注册所有已缓存的自定义组件
            ResourceManager.set_resource(self.resource)
            
            # 导入各个模块以触发装饰器注册
            from custom import fgo_actions
            from custom import farming_actions
            from custom import utility_actions
            
            # 获取已注册的组件列表
            recognitions = ResourceManager.get_registered_recognitions()
            actions = ResourceManager.get_registered_actions()
            
            logger.info(f"Registered {len(recognitions)} recognitions: {recognitions}")
            logger.info(f"Registered {len(actions)} actions: {actions}")
            
        except ImportError as e:
            logger.warning(f"Could not load custom actions: {e}")
        except Exception as e:
            logger.error(f"Error registering custom components: {e}")
    
    def init_tasker(self) -> bool:
        """初始化 Tasker"""
        if self.controller is None or self.resource is None:
            logger.error("Controller or Resource not initialized!")
            return False
        
        self.tasker = Tasker()
        
        if not self.tasker.bind(self.resource, self.controller):
            logger.error("Failed to bind tasker!")
            return False
        
        logger.info("Tasker initialized!")
        return True
    
    def run_task(self, entry: str, params: dict = None) -> bool:
        """
        运行任务
        
        Args:
            entry: Pipeline 入口节点名
            params: 任务参数
        """
        if self.tasker is None:
            logger.error("Tasker not initialized!")
            return False
        
        logger.info(f"Running task: {entry}")
        
        if params:
            param_str = json.dumps(params, ensure_ascii=False)
        else:
            param_str = "{}"
        
        job = self.tasker.post_task(entry, param_str)
        status = job.wait()
        
        if status.succeeded():
            logger.info(f"Task '{entry}' completed successfully!")
            return True
        else:
            logger.error(f"Task '{entry}' failed!")
            return False
    
    def run_detection_test(self):
        """运行检测测试"""
        if self.controller is None:
            logger.error("Controller not initialized!")
            return
        
        logger.info("=== Detection Test ===")
        
        # 截图
        job = self.controller.post_screencap()
        img = job.wait().get()
        
        logger.info(f"Screenshot: {img.shape}")
        
        # 保存截图
        import cv2
        debug_dir = Path(__file__).parent / "debug"
        debug_dir.mkdir(exist_ok=True)
        cv2.imwrite(str(debug_dir / "latest_screenshot.png"), img)
        logger.info(f"Saved to: {debug_dir / 'latest_screenshot.png'}")
    
    def close(self):
        """清理资源"""
        self.tasker = None
        self.controller = None
        self.resource = None


def main():
    parser = argparse.ArgumentParser(description="MaaFGO Runner")
    parser.add_argument("--address", "-a", help="ADB connection address")
    parser.add_argument("--task", "-t", default="MainInterface",
                        help="Task entry point (default: MainInterface)")
    parser.add_argument("--debug", "-d", action="store_true",
                        help="Enable debug mode")
    parser.add_argument("--test", action="store_true",
                        help="Run detection test only")
    
    args = parser.parse_args()
    
    # 调试模式设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("=" * 50)
    logger.info("  MaaFGO Runner")
    logger.info("=" * 50)
    
    runner = MaaFGORunner(debug=args.debug)
    
    try:
        # 连接设备
        if not runner.connect(args.address):
            return 1
        
        # 仅测试模式
        if args.test:
            runner.run_detection_test()
            return 0
        
        # 加载资源
        if not runner.load_resources():
            return 1
        
        # 初始化 Tasker
        if not runner.init_tasker():
            return 1
        
        # 运行任务
        if not runner.run_task(args.task):
            return 1
        
        logger.info("Done!")
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Interrupted by user.")
        return 130
    
    finally:
        runner.close()


if __name__ == "__main__":
    sys.exit(main())
