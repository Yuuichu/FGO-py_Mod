# 任务分解: 剧情跳过 (Story Skip)

## 任务总览

| ID | 任务 | 状态 | 依赖 | 优先级 |
|----|------|------|------|--------|
| T1 | 检查图像模板文件 | ✅ 已完成 | - | P0 |
| T2 | 验证检测方法参数 | ✅ 已完成 | T1 | P0 |
| T3 | 审查 skipStory 函数 | ✅ 已完成 | T2 | P0 |
| T4 | 验证多场景集成 | ✅ 已完成 | T3 | P0 |
| T5 | 代码清理和注释 | ✅ 已完成 | T4 | P1 |

**状态图例**: ⬜ 待开始 | 🔄 进行中 | ✅ 已完成 | ❌ 已取消

**优先级**: P0 (必须) | P1 (重要) | P2 (可选)

---

## 用户故事 1: 战斗中剧情自动跳过

### T1: 检查图像模板文件

**文件**: 
- `FGO-py/fgoImage/storymenu.png`
- `FGO-py/fgoImage/storyskipbutton.png`
- `FGO-py/fgoImage/storyskipconfirm.png`

**描述**: 确认模板文件存在、格式正确、尺寸合理

**验收标准**:
- [ ] 三个模板文件都存在
- [ ] 模板有正确的透明度通道（或黑色作为透明）
- [ ] 模板对应 1280×720 游戏画面

---

### T2: 验证检测方法参数

**文件**: `FGO-py/fgoDetect.py`

**描述**: 检查 `isStoryPlaying`, `isStorySkipButton`, `isStorySkipConfirm` 方法的参数

**需要验证**:
```python
# isStoryPlaying - 检测剧情菜单
rect=(1000, 400, 1280, 620)  # 右下角区域
threshold=0.25

# isStorySkipButton - 检测跳过按钮
rect=(1100, 0, 1280, 100)  # 右上角区域
threshold=0.05  # 默认值

# isStorySkipConfirm - 检测确认弹窗
rect=(550, 480, 1000, 620)  # 中间偏下区域
threshold=0.05  # 默认值
```

**验收标准**:
- [ ] rect 区域覆盖目标 UI 元素
- [ ] threshold 值在合理范围内
- [ ] 方法使用 `hasattr` 检查模板是否存在

---

### T3: 审查 skipStory 函数 [P]

**文件**: `FGO-py/fgoKernel.py`

**描述**: 审查 `skipStory()` 函数的逻辑和可靠性

**当前实现检查点**:
```python
def skipStory():
    # 1. 获取截图
    det = Detect(0, .3)
    
    # 2. 检测确认弹窗（优先处理）
    if hasConfirm:
        点击 (825, 557)
        return True
    
    # 3. 检测跳过按钮
    if hasSkipBtn:
        点击 (1189, 44)
        等待后检测确认弹窗
        return True
    
    return False
```

**验收标准**:
- [ ] 逻辑顺序正确（先确认弹窗后跳过按钮）
- [ ] 等待时间适当（不过长也不过短）
- [ ] 日志输出有用信息

---

### T4: 验证多场景集成

**文件**: `FGO-py/fgoKernel.py`

**描述**: 确认 `skipStory()` 在各处调用正确

**检查位置**:
1. `Battle.__call__` - 战斗主循环
2. `Main.__call__` - 主循环等待编队
3. `Main.chooseFriend` - 选择助战循环

**验收标准**:
- [ ] Battle 类的 `skipStoryEnabled` 属性工作正常
- [ ] 调用位置不会造成无限循环
- [ ] 不干扰正常的检测流程

---

## 用户故事 2: 代码质量

### T5: 代码清理和注释

**文件**: 
- `FGO-py/fgoDetect.py`
- `FGO-py/fgoKernel.py`

**描述**: 确保代码整洁、一致

**验收标准**:
- [ ] 无语法错误
- [ ] 无未使用的代码
- [ ] 关键方法有文档字符串

---

## 检查点

### 功能完成检查

- [ ] 所有 T1-T5 任务已完成
- [ ] 代码可正常运行
- [ ] 原有功能不受影响

---

## 完成总结

### 已完成任务

- ✅ T1: 图像模板文件检查 - 三个模板文件都存在且格式正确
- ✅ T2: 检测方法参数验证 - rect 区域和 threshold 值合理
- ✅ T3: skipStory 函数审查 - 逻辑正确，日志清晰
- ✅ T4: 多场景集成验证 - 在 Battle、Main、chooseFriend 中正确集成
- ✅ T5: 代码清理 - 无 linter 错误，代码风格一致

### 检查结果

**模板文件**:
- `storymenu.png` - 蓝色"记录"按钮，用于检测剧情界面
- `storyskipbutton.png` - 跳过按钮轮廓
- `storyskipconfirm.png` - 确认弹窗按钮

**检测参数**:
- `isStoryPlaying()`: rect=(1000,400,1280,620), threshold=0.25
- `isStorySkipButton()`: rect=(1100,0,1280,100), threshold=0.05
- `isStorySkipConfirm()`: rect=(550,480,1000,620), threshold=0.05

**集成位置**:
- `Battle.__call__` 第 462 行 - 战斗循环中
- `Main.__call__` 第 508、520 行 - 主循环中、等待编队时
- `Main.__call__` 第 549-553 行 - **战斗完成后** (新增)
- `Main.chooseFriend` 第 585 行 - 选择助战时

### 遗留问题

- 无

### 后续优化

- 支持不同服务器的模板差异（在 cn/jp/na/tw 子目录放置对应模板）
- 添加剧情跳过次数统计
- 支持更多类型的剧情界面
