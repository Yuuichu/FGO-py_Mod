#!/usr/bin/env python3
"""
MaaFGO POC Demo - 概念验证演示

用于验证 MaaFramework 与 FGO-py 集成的可行性。

功能：
1. 设备连接测试
2. 截图功能测试
3. 识别功能测试
4. 简单战斗流程测试

使用方法：
    python poc_demo.py                    # 自动检测设备
    python poc_demo.py --address 127.0.0.1:5555  # 指定ADB地址
    python poc_demo.py --list-devices     # 列出可用设备
"""

import argparse
import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "FGO-py"))

def check_dependencies():
    """检查依赖"""
    missing = []
    
    try:
        import maa
    except ImportError:
        missing.append("MaaFw")
    
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python")
    
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    return True


def list_devices():
    """列出可用设备"""
    from agent.device_adapter import find_adb_devices, find_win32_windows
    
    print("\n=== ADB Devices ===")
    devices = find_adb_devices()
    if devices:
        for name, address, adb_path in devices:
            print(f"  {name}: {address}")
    else:
        print("  (No devices found)")
    
    print("\n=== Win32 Windows ===")
    windows = find_win32_windows()
    if windows:
        for title, hwnd in windows[:10]:  # 只显示前10个
            if title:
                print(f"  [{hwnd}] {title}")
    else:
        print("  (No windows found)")


def test_connection(address: str = None):
    """测试设备连接"""
    from agent.device_adapter import MaaDeviceAdapter, find_adb_devices
    
    print("\n=== Connection Test ===")
    
    if address:
        print(f"Connecting to: {address}")
        device = MaaDeviceAdapter(address=address)
    else:
        print("Auto-detecting device...")
        devices = find_adb_devices()
        if not devices:
            print("ERROR: No ADB devices found")
            return None
        
        name, address, adb_path = devices[0]
        print(f"Found: {name} ({address})")
        device = MaaDeviceAdapter(adb_path=adb_path, address=address)
    
    if device.connect():
        print("SUCCESS: Device connected")
        return device
    else:
        print("ERROR: Connection failed")
        return None


def test_screenshot(device):
    """测试截图功能"""
    print("\n=== Screenshot Test ===")
    
    start = time.time()
    img = device.screenshot()
    elapsed = (time.time() - start) * 1000
    
    print(f"Screenshot shape: {img.shape}")
    print(f"Screenshot time: {elapsed:.1f}ms")
    
    # 保存截图
    import cv2
    output_path = Path(__file__).parent / "debug" / "screenshot_test.png"
    output_path.parent.mkdir(exist_ok=True)
    cv2.imwrite(str(output_path), img)
    print(f"Saved to: {output_path}")
    
    return img


def test_detection(img):
    """测试识别功能"""
    print("\n=== Detection Test ===")
    
    from agent.detect_adapter import MaaDetectAdapter
    
    detector = MaaDetectAdapter()
    detector.inject(img)
    
    tests = [
        ("Main Interface", detector.isMainInterface),
        ("Turn Begin", detector.isTurnBegin),
        ("Battle Formation", detector.isBattleFormation),
        ("Battle Finished", detector.isBattleFinished),
        ("Battle Continue", detector.isBattleContinue),
    ]
    
    for name, func in tests:
        try:
            result = func()
            status = "YES" if result else "no"
        except FileNotFoundError as e:
            status = f"MISSING: {e}"
        except Exception as e:
            status = f"ERROR: {e}"
        
        print(f"  {name}: {status}")


def test_pipeline_basic():
    """测试基本 Pipeline 执行"""
    print("\n=== Pipeline Test ===")
    
    try:
        from maa.resource import Resource
        from maa.tasker import Tasker
        
        resource_path = Path(__file__).parent / "resource"
        
        resource = Resource()
        resource.post_bundle(str(resource_path)).wait()
        print(f"Resource loaded from: {resource_path}")
        
        print("Pipeline test: READY")
        print("(Full test requires connected device)")
        
    except Exception as e:
        print(f"Pipeline test FAILED: {e}")


def run_battle_poc(device):
    """运行战斗 POC（仅演示，需要游戏处于战斗界面）"""
    print("\n=== Battle POC ===")
    print("This will execute one battle turn.")
    print("Make sure the game is at the battle screen with Attack button visible.")
    
    confirm = input("Continue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Skipped.")
        return
    
    from agent.detect_adapter import MaaDetectAdapter
    
    # 截图并检测
    img = device.screenshot()
    detector = MaaDetectAdapter()
    detector.inject(img)
    
    if not detector.isTurnBegin():
        print("ERROR: Attack button not found. Make sure you're in battle.")
        return
    
    print("Attack button detected. Executing turn...")
    
    # 点击 Attack
    device.click(1180, 660)
    time.sleep(2.0)
    
    # 选择卡牌
    card_positions = [(128, 500), (385, 500), (642, 500)]
    for i, pos in enumerate(card_positions):
        print(f"  Selecting card {i+1}...")
        device.click(*pos)
        time.sleep(0.3)
    
    print("Turn executed!")
    print("Waiting for animation...")
    time.sleep(3.0)
    
    # 再次截图检查状态
    img = device.screenshot()
    detector.inject(img)
    
    if detector.isBattleFinished():
        print("Battle finished!")
    elif detector.isTurnBegin():
        print("Ready for next turn.")
    else:
        print("Status unknown.")


def main():
    parser = argparse.ArgumentParser(description="MaaFGO POC Demo")
    parser.add_argument("--address", "-a", help="ADB connection address")
    parser.add_argument("--list-devices", "-l", action="store_true", 
                        help="List available devices")
    parser.add_argument("--battle", "-b", action="store_true",
                        help="Run battle POC (requires game in battle)")
    parser.add_argument("--skip-checks", action="store_true",
                        help="Skip dependency checks")
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("  MaaFGO POC Demo")
    print("=" * 50)
    
    # 依赖检查
    if not args.skip_checks and not check_dependencies():
        return 1
    
    # 列出设备
    if args.list_devices:
        list_devices()
        return 0
    
    # 连接测试
    device = test_connection(args.address)
    if device is None:
        return 1
    
    # 截图测试
    img = test_screenshot(device)
    
    # 识别测试
    test_detection(img)
    
    # Pipeline 测试
    test_pipeline_basic()
    
    # 战斗 POC
    if args.battle:
        run_battle_poc(device)
    
    print("\n" + "=" * 50)
    print("  POC Demo Complete")
    print("=" * 50)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
