# FGO-py 项目宪法 (Constitution)

## 项目概述

FGO-py 是一个用于 Fate/Grand Order (FGO) 手游的全智能自动化脚本程序，支持安卓简体中文/日本语/英语/繁体中文版本。

### 核心理念

- **智能战斗不间断，不靠礼装不用拐**
- 打破 3T 速刷的固有思维，回归克制队 xjbd 的游戏体验
- 无需配置即可无脑通过绝大部分非高难关卡

## 技术栈

### 核心技术

- **语言**: Python 3.11+
- **UI 框架**: PyQt6 (GUI), Flask (Web UI)
- **图像处理**: OpenCV, NumPy
- **设备连接**: ADB (Android Debug Bridge)
- **OCR**: 用于文本识别

### 运行环境

- Windows (主要支持)
- Linux/Android/Mac/Docker (通过适配支持)
- AidLux (安卓本地运行)
- AzurLaneAutoScript 集成

## 架构原则

### 1. 前后端分离

项目在设计时考虑到不同环境下运行的需求，完全前后端分离：
- GUI 入口: `fgoGui.py`
- CLI 入口: `fgoCli.py`
- Web 入口: `fgoWebServer.py`

### 2. 模块化设计

核心模块职责：
- `fgoKernel.py`: 战斗核心逻辑
- `fgoDetect.py`: 图像检测
- `fgoDevice.py`: 设备连接管理
- `fgoFarming.py`: 刷本逻辑
- `fgoConfig.py`: 配置管理
- `fgoOcr.py`: 文字识别
- `fgoMetadata.py`: 游戏元数据

### 3. 长期可维护性

- 所有与游戏进度相关的内容都允许用户自行制作/管理
- 无需定期维护也能继续使用
- 图像资源存放在 `fgoImage/` 目录

## 代码规范

### Python 风格

- 启用 Python 的 UTF-8 模式 (PEP 540)
- 使用 type hints 提高代码可读性
- 保持函数简洁，单一职责

### 命名约定

- 文件名: `fgo` 前缀 + 功能名 (如 `fgoConfig.py`)
- 类名: PascalCase
- 函数/变量: snake_case 或 camelCase (保持与现有代码一致)

### 图像资源

- 格式: PNG
- 分辨率: 对应 1280×720 游戏画面
- 黑色 (#000) 部分视作透明

## 功能边界

### 应该做的

- 智能战斗：技能释放、宝具使用、卡牌选择
- 助战筛选
- 体力管理（吃苹果）
- 自动完成每周任务
- 抽友情池、领邮箱狗粮、礼装强化
- 剧情跳过

### 不应该做的

- 不提供 3T 速刷方案
- 不破解或修改游戏程序
- 不干扰游戏服务器

## 测试原则

- 优先测试核心战斗逻辑
- 图像识别需要在真实游戏画面上验证
- 支持多分辨率屏幕测试

## 安全与合规

- 遵循 GNU AGPLv3 开源协议
- 任何修改或使用都需要开源
- 用户需知晓使用风险

## 国际化

支持多语言界面：
- 简体中文 (zh)
- 日本语 (ja)
- English (en)

对应的翻译文件: `fgoI18n.*.ts` / `fgoI18n.*.qm`
