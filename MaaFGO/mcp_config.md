# MaaMCP Cursor 配置指南

## 什么是 MaaMCP

MaaMCP 是基于 MaaFramework 的 MCP (Model Context Protocol) 服务器，为 AI 助手（如 Cursor）提供 Android 设备和 Windows 桌面自动化能力。

## 配置步骤

### 1. 打开 Cursor MCP 配置

在 Cursor 中打开设置，找到 MCP 配置部分，或直接编辑 `~/.cursor/mcp.json`。

### 2. 添加 MaaMCP 服务器

```json
{
  "mcpServers": {
    "maa-mcp": {
      "command": "python",
      "args": ["-m", "maa_mcp"]
    }
  }
}
```

### 3. 重启 Cursor

配置完成后重启 Cursor，MaaMCP 将自动启动。

## MaaMCP 提供的能力

一旦配置完成，AI 助手将能够：

1. **设备连接**
   - 自动发现 ADB 设备
   - 连接安卓模拟器或真机

2. **屏幕操作**
   - 截取设备屏幕
   - 执行点击、滑动、输入等操作

3. **图像识别**
   - 模板匹配
   - OCR 文字识别
   - 颜色匹配

4. **Pipeline 执行**
   - 运行预定义的任务流程
   - 调试和测试 Pipeline

## 使用示例

配置完成后，你可以直接让 AI 助手：

- "连接到模拟器并截图"
- "点击屏幕上的开始按钮"
- "识别屏幕上的文字"
- "运行 MainInterface 任务"

## 手动启动 MaaMCP

如果需要手动启动或调试：

```bash
python -m maa_mcp
```

## 相关链接

- [MaaMCP GitHub](https://github.com/MaaXYZ/MaaMCP)
- [MCP 协议文档](https://modelcontextprotocol.io/)
