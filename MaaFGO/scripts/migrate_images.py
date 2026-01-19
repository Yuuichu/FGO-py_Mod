#!/usr/bin/env python3
"""
图像资源迁移脚本

将 FGO-py 的图像资源迁移到 MaaFGO 的资源目录。
MaaFramework 要求图像基于 720p 分辨率。

使用方法：
    python migrate_images.py           # 迁移基础图像
    python migrate_images.py --all     # 迁移所有图像
    python migrate_images.py --region cn  # 仅迁移指定区域
"""

import argparse
import shutil
from pathlib import Path

# 路径配置
SCRIPT_DIR = Path(__file__).parent
MAAFGO_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = MAAFGO_ROOT.parent
FGO_IMAGE_DIR = PROJECT_ROOT / "FGO-py" / "fgoImage"
MAA_IMAGE_DIR = MAAFGO_ROOT / "resource" / "image"

# 基础图像列表（Pipeline 需要的核心图像）
CORE_IMAGES = [
    "menu.png",           # 主界面
    "attack.png",         # Attack 按钮
    "battlebegin.png",    # 开始战斗按钮
    "battlecontinue.png", # 继续战斗按钮
    "dropitem.png",       # 掉落界面
    "defeated.png",       # 战败界面
    "networkerror.png",   # 网络错误
    "choosefriend.png",   # 选择好友
    "choosefriendex.png", # 选择好友（扩展）
    "support.png",        # 助战标志
    "still.png",          # 技能冷却
    "cross.png",          # 关闭按钮
    "close.png",          # 关闭按钮
    "skillerror.png",     # 技能错误
    # 卡牌颜色
    "arts.png",
    "quick.png", 
    "buster.png",
    # 克制标志
    "weak.png",
    "resist.png",
    # 暴击星
    "critical0.png",
    "critical1.png",
    "critical2.png",
    "critical3.png",
    "critical4.png",
    "critical5.png",
    "critical6.png",
    "critical7.png",
    "critical8.png",
    "critical9.png",
    # 充能条
    "charge0.png",
    "charge1.png",
    "charge2.png",
    # 其他
    "listbar.png",
    "teamindex.png",
    "synthesis.png",
    "decidedisabled.png",
    "fpsummon.png",
    "fpcontinue.png",
    "addfriend.png",
    "nofriend.png",
    "apempty.png",
    "summonhistory.png",
    # 剧情跳过
    "storymenu.png",
    "storyskipbutton.png",
    "storyskipconfirm.png",
    # 卡牌封印
    "cardsealedarts.png",
    "cardsealedquick.png",
    "cardsealedbuster.png",
    "charasealed.png",
    "hougusealed.png",
    # 阶段标识
    "stage1.png",
    "stage2.png",
    "stage3.png",
    "rainbow.png",
]

# 区域特定图像（需要从区域目录复制）
REGION_IMAGES = [
    # 各区域通用
]

# 区域列表
REGIONS = ["cn", "jp", "na", "tw"]


def copy_image(src: Path, dst: Path, verbose: bool = True):
    """复制单个图像"""
    if not src.exists():
        if verbose:
            print(f"  SKIP (not found): {src.name}")
        return False
    
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    
    if verbose:
        print(f"  COPY: {src.name}")
    return True


def migrate_core_images(verbose: bool = True):
    """迁移核心图像"""
    print("\n=== Migrating Core Images ===")
    
    copied = 0
    skipped = 0
    
    for img_name in CORE_IMAGES:
        src = FGO_IMAGE_DIR / img_name
        dst = MAA_IMAGE_DIR / img_name
        
        if copy_image(src, dst, verbose):
            copied += 1
        else:
            skipped += 1
    
    print(f"\nCore: {copied} copied, {skipped} skipped")
    return copied, skipped


def migrate_region_images(region: str, verbose: bool = True):
    """迁移区域特定图像"""
    print(f"\n=== Migrating {region.upper()} Region Images ===")
    
    src_dir = FGO_IMAGE_DIR / region
    dst_dir = MAA_IMAGE_DIR / region
    
    if not src_dir.exists():
        print(f"  Source directory not found: {src_dir}")
        return 0, 0
    
    copied = 0
    skipped = 0
    
    for img_path in src_dir.glob("*.png"):
        dst = dst_dir / img_path.name
        if copy_image(img_path, dst, verbose):
            copied += 1
        else:
            skipped += 1
    
    print(f"\n{region.upper()}: {copied} copied, {skipped} skipped")
    return copied, skipped


def migrate_all(verbose: bool = True):
    """迁移所有图像"""
    total_copied = 0
    total_skipped = 0
    
    # 核心图像
    copied, skipped = migrate_core_images(verbose)
    total_copied += copied
    total_skipped += skipped
    
    # 各区域图像
    for region in REGIONS:
        copied, skipped = migrate_region_images(region, verbose)
        total_copied += copied
        total_skipped += skipped
    
    print(f"\n=== Total: {total_copied} copied, {total_skipped} skipped ===")


def create_symlinks():
    """创建符号链接（可选，用于开发）"""
    print("\n=== Creating Symlinks ===")
    print("Note: This requires admin privileges on Windows")
    
    # 这个功能在 Windows 上需要管理员权限
    # 暂时跳过
    print("Skipped (not implemented for Windows)")


def main():
    parser = argparse.ArgumentParser(description="Migrate FGO-py images to MaaFGO")
    parser.add_argument("--all", action="store_true", help="Migrate all images")
    parser.add_argument("--region", "-r", choices=REGIONS,
                        help="Migrate specific region only")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Quiet mode")
    parser.add_argument("--symlink", action="store_true",
                        help="Create symlinks instead of copying")
    
    args = parser.parse_args()
    verbose = not args.quiet
    
    print("=" * 50)
    print("  FGO Image Migration Tool")
    print("=" * 50)
    print(f"Source: {FGO_IMAGE_DIR}")
    print(f"Target: {MAA_IMAGE_DIR}")
    
    if args.symlink:
        create_symlinks()
    elif args.all:
        migrate_all(verbose)
    elif args.region:
        migrate_region_images(args.region, verbose)
    else:
        migrate_core_images(verbose)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
