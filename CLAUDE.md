# CLAUDE.md - FGO-py AI 助手指令

本文件为 AI 编码助手提供项目上下文和工作指南。

## 项目概述

FGO-py 是一个用于 Fate/Grand Order 手游的全智能自动化脚本，支持安卓简中/日服/美服/台服。

**核心理念**: 智能战斗不间断，不靠礼装不用拐

## 快速入门

### 目录结构

```
FGO-py/              # 主程序目录
├── fgo.py           # 程序入口
├── fgoKernel.py     # 战斗核心逻辑
├── fgoDetect.py     # 图像检测
├── fgoDevice.py     # 设备连接
├── fgoConfig.py     # 配置管理
├── fgoGui.py        # GUI 入口
├── fgoCli.py        # CLI 入口
├── fgoWebServer.py  # Web 入口
├── fgoImage/        # 图像资源
└── ...

memory/              # 项目宪法和长期记忆
specs/               # 功能规范文档
templates/           # 文档模板
scripts/             # spec-kit 脚本
```

### 运行程序

```bash
# GUI 模式
python FGO-py/fgo.py gui

# CLI 模式
python FGO-py/fgo.py cli

# Web 模式
python FGO-py/fgo.py web
```

### 技术栈

- Python 3.11+
- PyQt6 (GUI)
- OpenCV + NumPy (图像处理)
- ADB (设备连接)

## 核心文件说明

| 文件 | 职责 |
|------|------|
| `fgoKernel.py` | 战斗核心逻辑、技能释放、卡牌选择 |
| `fgoDetect.py` | 图像模板匹配、屏幕状态检测 |
| `fgoDevice.py` | ADB 设备连接和操作 |
| `fgoFarming.py` | 自动刷本逻辑 |
| `fgoConfig.py` | 配置文件读写 |
| `fgoOcr.py` | OCR 文字识别 |
| `fgoMetadata.py` | 游戏从者/技能元数据 |

## 编码规范

### Python 风格

- UTF-8 编码 (PEP 540)
- 使用 type hints
- 函数保持单一职责

### 命名约定

- 文件名: `fgo` + 功能名 (如 `fgoConfig.py`)
- 保持与现有代码风格一致

### 图像资源

- 格式: PNG
- 分辨率: 对应 1280×720
- 黑色 (#000) 视作透明

## Spec-Kit 工作流

### 1. 创建功能规范

```bash
./scripts/create-new-feature.sh <feature-name>
```

### 2. 编写规范 → 计划 → 任务

1. 在 `specs/<feature-name>/spec.md` 编写功能规范
2. 在 `specs/<feature-name>/plan.md` 编写实现计划
3. 在 `specs/<feature-name>/tasks.md` 分解具体任务

### 3. 实现功能

按 `tasks.md` 中的任务顺序实现，更新任务状态。

## 注意事项

### 应该做

- 参考 `memory/constitution.md` 了解项目原则
- 阅读现有代码理解风格和约定
- 在修改核心逻辑前先理解整体架构
- 保持向后兼容

### 不应该做

- 不破坏现有配置文件格式
- 不引入不必要的依赖
- 不删除用户自定义的图像资源

## 相关链接

- [项目 README](readme.md)
- [版本记录](doc/versions.md)
- [项目宪法](memory/constitution.md)
