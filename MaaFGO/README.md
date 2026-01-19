# MaaFGO - 基于 MaaFramework 的 FGO 自动化

本目录包含将 FGO-py 迁移到 MaaFramework 的相关资源。

## 目录结构

```
MaaFGO/
├── interface.json          # MaaFramework 项目接口配置
├── poc_demo.py             # POC 演示脚本
├── run_with_maa.py         # 完整运行脚本
├── agent/                  # Python 集成模块
│   ├── __init__.py
│   ├── device_adapter.py   # 设备控制层适配器
│   └── detect_adapter.py   # 识别层适配器
├── custom/
│   └── fgo_actions.py      # 自定义识别器和动作
├── resource/
│   ├── image/              # 图像模板资源（已迁移）
│   │   ├── cn/             # 简中服专用图像
│   │   ├── jp/             # 日服专用图像
│   │   ├── na/             # 美服专用图像
│   │   └── tw/             # 台服专用图像
│   ├── model/
│   │   └── ocr/            # OCR 模型文件
│   └── pipeline/           # Pipeline JSON 任务流程
│       └── main.json       # 主任务流程
├── scripts/
│   └── migrate_images.py   # 图像迁移脚本
├── config/
│   └── maa_pi_config.json  # MaaPiCli 配置
└── debug/                  # 调试输出目录
```

## 快速开始

### 1. 安装依赖

```bash
pip install MaaFw opencv-python numpy
```

### 2. 运行 POC 演示

```bash
# 列出可用设备
python poc_demo.py --list-devices

# 自动连接并测试
python poc_demo.py

# 指定 ADB 地址
python poc_demo.py --address 127.0.0.1:5555

# 执行战斗 POC（需要游戏处于战斗界面）
python poc_demo.py --battle
```

### 3. 使用完整运行器

```bash
# 运行检测测试
python run_with_maa.py --test

# 运行主界面检测任务
python run_with_maa.py --task MainInterface

# 运行自动刷本任务
python run_with_maa.py --task AutoFarming
```

### 4. 迁移图像资源

```bash
# 迁移核心图像
python scripts/migrate_images.py

# 迁移所有图像（包括区域特定）
python scripts/migrate_images.py --all

# 迁移特定区域
python scripts/migrate_images.py --region cn
```

## 开发工具

### Python SDK

- **MaaFw**: MaaFramework Python SDK
- **MaaDebugger**: Pipeline 调试器

```bash
# 启动 MaaDebugger
python -m MaaDebugger
```

### 本地开发工具 (tools/ 目录)

- **MFAToolsPlus**: 跨平台开发工具箱
- **MaaPipelineEditor**: 可视化 Pipeline 编辑器
- **MaaInspector**: 基于 vue-flow 的可视化编辑器
- **MaaLogAnalyzer**: 日志分析工具

### VSCode 插件

请在 VSCode 扩展商店搜索安装 `maa-support` 插件。

## 核心模块说明

### MaaDeviceAdapter (agent/device_adapter.py)

设备控制层适配器，用 MaaFramework 的 Controller 替代 fgoDevice：

```python
from agent.device_adapter import MaaDeviceAdapter, connect_device

# 连接设备
device = connect_device(address="127.0.0.1:5555")

# 截图
img = device.screenshot()

# 触摸操作（兼容 fgoDevice 接口）
device.touch((640, 400), wait=500)

# 滑动
device.swipe((400, 600), (400, 200))
```

### MaaDetectAdapter (agent/detect_adapter.py)

识别层适配器，兼容 fgoDetect 的检测接口：

```python
from agent.detect_adapter import MaaDetectAdapter

detector = MaaDetectAdapter()
detector.inject(img)

# 状态检测
if detector.isMainInterface():
    print("在主界面")
if detector.isTurnBegin():
    print("回合开始")

# 卡牌识别
colors = detector.getCardColor()
```

### Custom Actions (custom/fgo_actions.py)

自定义 MaaFramework 动作，封装 FGO-py 的战斗逻辑：

- `FGO_TurnRecognition`: 回合状态识别
- `FGO_TurnAction`: 回合执行（Attack + 选卡）
- `FGO_SmartTurnAction`: 智能回合（含宝具）
- `FGO_CastSkill`: 释放技能
- `FGO_CastMasterSkill`: 御主技能
- `FGO_CollectRewards`: 收集奖励

## Pipeline 开发

### 基本节点

```json
{
    "节点名称": {
        "recognition": "TemplateMatch",
        "template": "image.png",
        "threshold": 0.9,
        "roi": [x, y, w, h],
        "action": "Click",
        "next": ["下一个节点"]
    }
}
```

### 使用自定义动作

```json
{
    "ExecuteTurn": {
        "recognition": "Custom",
        "custom_recognition": "FGO_TurnRecognition",
        "action": "Custom",
        "custom_action": "FGO_TurnAction",
        "next": ["CheckBattleFinished", "WaitTurnBegin"]
    }
}
```

## 迁移进度

- [x] 设备控制层 (fgoDevice → MaaDeviceAdapter)
- [x] 图像检测层 (fgoDetect → MaaDetectAdapter)
- [x] 战斗核心 (fgoKernel.Turn → Custom Action)
- [x] 核心图像资源迁移
- [x] OCR 模型集成 (ppocr_v3: zh_cn, ja_jp, en_us, zh_tw)
- [x] 完整刷本逻辑 (fgoKernel.Main/Battle → Pipeline)
- [x] 配置界面 (interface.json + config_ui.py)
- [x] 实用功能 (友情点召唤、邮箱收取等)
- [ ] 多服务器资源支持

## 配置界面

提供 CLI 和 GUI 两种配置方式：

```bash
# CLI 交互模式
python config_ui.py

# GUI 模式（需要 tkinter）
python config_ui.py --gui

# 列出所有任务
python config_ui.py --list

# 直接运行指定任务
python config_ui.py --run "自动刷本"
```

### 可配置选项

| 选项 | 说明 |
|------|------|
| Server | 服务器选择（CN/JP/NA/TW） |
| AppleType | 苹果类型（金/银/铜/彩虹/不吃） |
| TeamConfig | 队伍选择（1-10） |
| BattleCount | 刷本次数 |
| AutoFormation | 自动编队 |
| SkipStory | 剧情跳过 |

## OCR 模型

已从 [MaaCommonAssets](https://github.com/MaaXYZ/MaaCommonAssets/tree/main/OCR) 集成 PaddleOCR v3 模型：

| 语言 | 目录 | 用途 |
|------|------|------|
| 简体中文 | `model/ocr/zh_cn` | 简中服 (CN) |
| 日语 | `model/ocr/ja_jp` | 日服 (JP) |
| 英语 | `model/ocr/en_us` | 美服 (NA) |
| 繁体中文 | `model/ocr/zh_tw` | 台服 (TW) |

OCR 相关的 Pipeline 节点定义在 `resource/pipeline/ocr_tasks.json` 中

## 参考文档

- [MaaFramework 官方文档](https://maafw.xyz/)
- [Pipeline 协议](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/3.1-任务流水线协议.md)
- [Python SDK 示例](https://github.com/MaaXYZ/MaaFramework/tree/main/sample/python)
