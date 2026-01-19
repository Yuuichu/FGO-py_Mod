# MaaFGO 服务层架构

## 概述

服务层是 MaaFGO.Avalonia 的核心业务逻辑层，封装 MaaFramework 功能并提供高级抽象。

## 服务列表

### 1. MaaService (已实现)

**文件**: `Services/MaaService.cs`

**职责**: MaaFramework 核心功能封装

```csharp
public class MaaService : IDisposable
{
    // 单例访问
    public static MaaService Instance { get; }
    
    // 设备管理
    Task<List<DeviceInfo>> FindDevicesAsync();
    Task<bool> ConnectAsync(string address, string? adbPath = null);
    Task DisconnectAsync();
    
    // 任务执行
    Task<bool> RunTaskAsync(string entry, string param = "{}");
    void Stop();
    
    // 截图
    Task<byte[]?> ScreencapAsync();
}
```

### 2. ConfigService

**文件**: `Services/ConfigService.cs`

**职责**: 配置管理，包括战斗脚本、苹果策略、服务器设置等

```csharp
public class ConfigService
{
    // 配置加载/保存
    void Load();
    void Save();
    
    // 通用配置
    ServerType Server { get; set; }          // CN/JP/NA/TW
    AppleType AppleStrategy { get; set; }    // 苹果策略
    int BattleCount { get; set; }            // 刷本次数
    int TeamIndex { get; set; }              // 队伍索引
    
    // 战斗脚本
    List<BattleScript> BattleScripts { get; set; }
    BattleScript? CurrentScript { get; set; }
    
    // 好友筛选
    FriendFilter FriendFilter { get; set; }
}
```

### 3. BattleService

**文件**: `Services/BattleService.cs`

**职责**: 战斗逻辑封装，包括技能释放、选卡策略

```csharp
public class BattleService
{
    // 战斗状态
    BattleState State { get; }
    
    // 技能操作
    Task<bool> CastSkillAsync(int servant, int skill, int? target = null);
    Task<bool> CastMasterSkillAsync(int skill, int? target1 = null, int? target2 = null);
    
    // 选卡操作
    Task<bool> SelectCardsAsync(int[] cardOrder);
    Task<bool> SmartSelectCardsAsync();  // 智能选卡
    
    // 宝具操作
    Task<bool> UseNoblePhantasmAsync(int[] servants);
    
    // 执行战斗脚本
    Task<bool> ExecuteScriptAsync(BattleScript script);
    
    // 状态检测
    Task<TurnInfo> GetTurnInfoAsync();
}
```

### 4. FriendService

**文件**: `Services/FriendService.cs`

**职责**: 好友助战选择逻辑

```csharp
public class FriendService
{
    // 好友选择
    Task<bool> SelectFriendAsync(FriendFilter filter);
    Task<bool> RefreshFriendListAsync();
    
    // 好友检测
    Task<List<FriendInfo>> DetectFriendsAsync();
    Task<FriendInfo?> FindMatchingFriendAsync(FriendFilter filter);
}
```

### 5. CustomActionService

**文件**: `Services/CustomActionService.cs`

**职责**: MaaFramework 自定义动作/识别器的注册和管理

```csharp
public class CustomActionService
{
    // 注册自定义动作
    void RegisterActions(MaaResource resource);
    
    // 动作回调
    event Action<string, object?>? OnActionExecuted;
    
    // 可用动作列表
    IReadOnlyList<string> AvailableActions { get; }
    IReadOnlyList<string> AvailableRecognitions { get; }
}
```

### 6. LoggingService

**文件**: `Services/LoggingService.cs`

**职责**: 统一日志管理

```csharp
public class LoggingService
{
    // 日志记录
    void Info(string message);
    void Warning(string message);
    void Error(string message, Exception? ex = null);
    void Debug(string message);
    
    // 日志事件（用于 UI 显示）
    event Action<LogEntry>? OnLogAdded;
    
    // 日志历史
    IReadOnlyList<LogEntry> Logs { get; }
    void Clear();
}
```

## 数据模型

### ServerType

```csharp
public enum ServerType
{
    CN,  // 简中服
    JP,  // 日服
    NA,  // 美服
    TW   // 台服
}
```

### AppleType

```csharp
public enum AppleType
{
    None,      // 不吃苹果
    Bronze,    // 铜苹果
    Silver,    // 银苹果
    Gold,      // 金苹果
    Rainbow    // 彩苹果
}
```

### BattleScript

```csharp
public class BattleScript
{
    public string Name { get; set; }
    public List<TurnScript> Turns { get; set; }
}

public class TurnScript
{
    public int Turn { get; set; }
    public int Stage { get; set; }
    public List<SkillAction> Skills { get; set; }
    public List<int> NoblePhantasms { get; set; }  // 使用宝具的从者索引
}

public class SkillAction
{
    public int Servant { get; set; }  // 0-2: 从者, 3: 御主
    public int Skill { get; set; }    // 0-2
    public int? Target1 { get; set; }
    public int? Target2 { get; set; } // 换人用
}
```

### BattleState

```csharp
public class BattleState
{
    public int Stage { get; set; }
    public int StageTotal { get; set; }
    public int Turn { get; set; }
    public int StageTurn { get; set; }
    
    public int[] ServantHP { get; set; }
    public int[] ServantNP { get; set; }
    public int[][] SkillCooldown { get; set; }
    public int[] MasterSkillCooldown { get; set; }
}
```

### TurnInfo

```csharp
public class TurnInfo
{
    public CardInfo[] Cards { get; set; }      // 5张卡牌
    public bool[] NoblePhantasmReady { get; set; }  // 3个宝具是否可用
    public int[] EnemyHP { get; set; }
}

public class CardInfo
{
    public CardColor Color { get; set; }  // Arts/Quick/Buster
    public int ServantIndex { get; set; }
    public bool IsSealed { get; set; }
    public float CriticalRate { get; set; }
    public ResistType Resist { get; set; }
}
```

### FriendFilter

```csharp
public class FriendFilter
{
    public string? ServantName { get; set; }
    public ServantClass? Class { get; set; }
    public int? MinSkillLevel { get; set; }
    public string? CraftEssence { get; set; }
    public bool PreferFriend { get; set; }
}
```

### LogEntry

```csharp
public class LogEntry
{
    public DateTime Timestamp { get; set; }
    public LogLevel Level { get; set; }
    public string Message { get; set; }
}
```

## 依赖关系

```
┌─────────────────┐
│  LoggingService │ ← 被所有服务依赖
└─────────────────┘
         ↑
┌─────────────────┐
│   ConfigService │ ← 配置信息
└─────────────────┘
         ↑
┌─────────────────┐
│    MaaService   │ ← 核心服务
└─────────────────┘
    ↑         ↑
┌───────┐ ┌────────────────────┐
│Battle │ │CustomActionService │
│Service│ └────────────────────┘
└───────┘
    ↑
┌───────────────┐
│ FriendService │
└───────────────┘
```

## 使用示例

### ViewModel 中使用服务

```csharp
public partial class MainWindowViewModel : ViewModelBase
{
    private readonly MaaService _maaService;
    private readonly ConfigService _configService;
    private readonly BattleService _battleService;
    private readonly LoggingService _loggingService;

    public MainWindowViewModel()
    {
        _loggingService = LoggingService.Instance;
        _configService = ConfigService.Instance;
        _maaService = MaaService.Instance;
        _battleService = new BattleService(_maaService);
        
        _loggingService.OnLogAdded += log => 
        {
            LogText += $"[{log.Timestamp:HH:mm:ss}] {log.Message}\n";
        };
    }

    [RelayCommand]
    private async Task StartFarmingAsync()
    {
        _loggingService.Info("开始刷本...");
        
        // 使用配置
        var script = _configService.CurrentScript;
        var count = _configService.BattleCount;
        
        for (int i = 0; i < count; i++)
        {
            await _maaService.RunTaskAsync("Farming_Start");
        }
        
        _loggingService.Info($"完成 {count} 次刷本");
    }
}
```

## 测试策略

每个服务应有对应的单元测试：

- `MaaServiceTests.cs` - 设备连接、任务执行测试
- `ConfigServiceTests.cs` - 配置加载/保存测试
- `BattleServiceTests.cs` - 战斗逻辑测试
- `FriendServiceTests.cs` - 好友选择测试

## 扩展点

### 添加新服务

1. 在 `Services/` 目录创建服务类
2. 实现单例模式或依赖注入
3. 在 `App.axaml.cs` 中注册服务
4. 更新此文档

### 添加新配置项

1. 在 `ConfigService` 中添加属性
2. 更新 `Load()` 和 `Save()` 方法
3. 在 UI 中添加配置界面
