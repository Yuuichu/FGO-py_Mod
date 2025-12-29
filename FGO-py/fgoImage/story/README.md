# 剧情跳过功能图片资源

本目录包含剧情跳过功能的说明文档。

## ⚠️ 重要：图片存放位置

图片需要放在 `fgoImage/` 根目录下（与 `menu.png` 等文件同级），而不是这个 `story/` 子目录！

## 需要的图片

### 1. storymenu.png (必需)
- **存放位置**: `fgoImage/storymenu.png`
- **用途**: 检测是否处于剧情播放界面
- **截图区域**: 剧情界面右上角的菜单按钮 (Menu)
- **检测坐标**: (1188, 0) 到 (1280, 72)
- **示例**: 剧情界面右上角的三条横线菜单图标或 "Menu" 按钮

### 2. storyskipconfirm.png (必需)
- **存放位置**: `fgoImage/storyskipconfirm.png`
- **用途**: 检测跳过剧情确认弹窗
- **截图区域**: 跳过确认弹窗的特征部分（如"确定"按钮）
- **检测坐标**: (380, 360) 到 (900, 520)

## 截图要求

1. **分辨率**: 所有图片必须对应 **1280×720** 的游戏画面分辨率
2. **格式**: PNG 格式，必须有 Alpha 透明通道
3. **透明处理**: 黑色 (#000000) 区域会被视为透明（用于忽略不稳定的区域）

## 如何截图

使用项目自带的截图功能：
- **GUI**: 点击「检查截图」按钮
- **CLI**: 使用 `screenshot` 指令

## 制作步骤

1. 启动 FGO-py 并连接设备
2. 手动进入游戏的剧情播放界面
3. 使用上述截图功能截取完整画面 (会保存为 1280×720 的图片)
4. 用图片编辑软件 (如 Photoshop/GIMP) 打开截图
5. 裁剪出需要检测的区域
6. 将不需要匹配的区域填充为纯黑色 (#000000)
7. 保存为带 Alpha 通道的 PNG 格式
8. 将文件放入 `fgoImage/` 目录

## 不同服务器的图片

如果你使用的是不同服务器，可以将对应的图片放在服务器专用目录：
- 国服: `fgoImage/cn/storymenu.png` 和 `fgoImage/cn/storyskipconfirm.png`
- 日服: `fgoImage/jp/storymenu.png` 和 `fgoImage/jp/storyskipconfirm.png`
- 美服: `fgoImage/na/storymenu.png` 和 `fgoImage/na/storyskipconfirm.png`
- 台服: `fgoImage/tw/storymenu.png` 和 `fgoImage/tw/storyskipconfirm.png`

通用图片放在 `fgoImage/` 根目录，会作为默认检测图片。

## 跳过流程说明

自动跳过剧情的流程：
1. 检测到 `storymenu.png` 图片 → 判断当前在剧情界面
2. 点击右上角菜单按钮 (坐标: 1234, 36)
3. 点击跳过按钮 (坐标: 640, 400)
4. 检测到 `storyskipconfirm.png` → 点击确认 (坐标: 640, 440)

如果你的游戏版本按钮位置不同，可能需要修改 `fgoKernel.py` 中 `skipStory()` 函数的坐标。

