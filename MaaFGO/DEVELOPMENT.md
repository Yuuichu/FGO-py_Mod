# MaaFGO 开发指南

本文档帮助开发者快速配置开发环境，使用 Cursor IDE 进行 MaaFGO 项目开发。

## 开发环境要求

### 基础环境

| 工具 | 版本 | 用途 |
|------|------|------|
| .NET SDK | 8.0+ | Avalonia GUI 开发 |
| Python | 3.10+ | 脚本开发和 MaaFramework Python SDK |
| Node.js | 18+ | MaaDebugger 和工具 |
| Git | 2.30+ | 版本控制 |

### 推荐 IDE

- **Cursor** (首选) - AI 辅助开发
- Visual Studio Code - 需安装扩展

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/user/MaaFGO.git
cd MaaFGO
```

### 2. 安装依赖

```bash
# Python 依赖
pip install MaaFw opencv-python numpy serilog

# .NET 项目恢复
cd src/MaaFGO.Avalonia
dotnet restore
```

### 3. 下载开发工具

开发工具需要单独下载到 `tools/` 目录（已在 .gitignore 中忽略）：

| 工具 | 下载地址 | 用途 |
|------|----------|------|
| MFAToolsPlus | [GitHub Release](https://github.com/SweetSmellFox/MFATools) | 跨平台开发工具箱 |
| MaaDebugger | `pip install MaaDebugger` | Pipeline 调试器 |
| MaaInspector | [GitHub](https://github.com/neko-para/MaaInspector) | 可视化 Pipeline 编辑器 |
| MaaLogAnalyzer | [GitHub](https://github.com/MaaXYZ/MaaLogAnalyzer) | 日志分析工具 |
| MaaPipelineEditor | [GitHub](https://github.com/MaaXYZ/MaaPipelineEditor) | Pipeline 编辑器 |

```bash
# 安装 MaaDebugger
pip install MaaDebugger

# 启动 MaaDebugger
python -m MaaDebugger
```

## Cursor IDE 配置

### 推荐扩展

在 Cursor/VSCode 中安装以下扩展：

1. **maa-support** - MaaFramework 开发支持
   - Pipeline JSON 语法高亮和验证
   - 自动补全
   - 跳转到定义

2. **C# Dev Kit** - .NET 开发支持

3. **Python** - Python 开发支持

4. **Avalonia for VSCode** - Avalonia XAML 支持

### 工作区设置

创建 `.vscode/settings.json`（已被 gitignore）：

```json
{
    "files.associations": {
        "*.json": "json"
    },
    "json.schemas": [
        {
            "fileMatch": ["**/pipeline/*.json"],
            "url": "https://raw.githubusercontent.com/MaaXYZ/MaaFramework/main/tools/pipeline.schema.json"
        }
    ],
    "editor.formatOnSave": true,
    "python.defaultInterpreterPath": "python",
    "[csharp]": {
        "editor.defaultFormatter": "ms-dotnettools.csharp"
    }
}
```

### Cursor 规则

本项目在 `MaaFramework/AGENTS.md` 中定义了 Agent 规则，Cursor 会自动读取并遵循这些规则进行开发。

主要规则包括：
- Pipeline 协议规范
- 代码风格指南
- 命名约定

## 项目结构

```
MaaFGO/
├── specs/                      # 项目规格文档
│   ├── PROJECT_GOALS.md        # 项目目标
│   └── SERVICES_ARCHITECTURE.md # 服务层架构
├── src/MaaFGO.Avalonia/        # Avalonia GUI 项目
│   ├── Services/               # 服务层
│   │   ├── MaaService.cs       # MaaFramework 核心封装
│   │   ├── ConfigService.cs    # 配置管理
│   │   ├── BattleService.cs    # 战斗逻辑
│   │   ├── FriendService.cs    # 好友选择
│   │   ├── CustomActionService.cs # 自定义动作
│   │   └── LoggingService.cs   # 日志服务
│   └── ViewModels/             # MVVM 视图模型
├── custom/                     # Python 自定义动作
│   ├── fgo_actions.py          # FGO 自定义动作
│   ├── battle_logic.py         # 战斗逻辑
│   └── ...
├── agent/                      # Python 适配器
│   ├── device_adapter.py       # 设备适配器
│   └── detect_adapter.py       # 检测适配器
├── resource/                   # MaaFramework 资源
│   ├── pipeline/               # Pipeline JSON
│   ├── image/                  # 图像模板
│   └── model/ocr/              # OCR 模型
└── tools/                      # 开发工具（不提交）
```

## 开发工作流

### 1. Pipeline 开发

使用 MaaDebugger 调试 Pipeline：

```bash
# 启动调试器
python -m MaaDebugger

# 或使用本地脚本
python scripts/start_maadebugger.ps1
```

### 2. 自定义动作开发

在 `custom/` 目录下添加 Python 自定义动作：

```python
from maa.custom_action import CustomAction
from maa.context import Context

class MyAction(CustomAction):
    def run(self, context: Context, argv) -> bool:
        # 实现逻辑
        return True
```

### 3. GUI 开发

在 `src/MaaFGO.Avalonia/` 目录下开发：

```bash
cd src/MaaFGO.Avalonia
dotnet build
dotnet run
```

### 4. 测试

```bash
# 运行 Python 测试
python run_with_maa.py --test

# 运行 POC 演示
python poc_demo.py --list-devices
python poc_demo.py --battle
```

## MCP 服务器配置

本项目使用 MCP（Model Context Protocol）服务器来增强 Cursor 的能力：

### cursor-browser-extension

用于前端/webapp 开发和测试。

### 配置方法

在 Cursor 设置中添加 MCP 服务器配置，详见 `mcp_config.md`。

## 常见问题

### Q: MaaFramework 找不到？

MaaFramework 是外部依赖，需要单独安装：

```bash
pip install MaaFw
```

或从 [MaaFramework Releases](https://github.com/MaaXYZ/MaaFramework/releases) 下载。

### Q: 设备连接失败？

1. 确保 ADB 已安装并在 PATH 中
2. 确保模拟器/设备已启动
3. 运行 `adb devices` 检查连接

### Q: Pipeline 验证失败？

确保安装了 maa-support VSCode 扩展，它会提供 Schema 验证。

## 参考资料

- [MaaFramework 官方文档](https://maafw.xyz/)
- [Pipeline 协议](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/3.1-任务流水线协议.md)
- [Avalonia 文档](https://docs.avaloniaui.net/)
- [项目目标](specs/PROJECT_GOALS.md)
- [服务层架构](specs/SERVICES_ARCHITECTURE.md)

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 联系方式

如有问题，请在 GitHub Issues 中提出。
