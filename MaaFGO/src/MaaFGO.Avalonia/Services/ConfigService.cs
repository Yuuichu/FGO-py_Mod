using Serilog;
using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace MaaFGO.Avalonia.Services;

/// <summary>
/// 服务器类型
/// </summary>
public enum ServerType
{
    CN,  // 简中服
    JP,  // 日服
    NA,  // 美服
    TW   // 台服
}

/// <summary>
/// 苹果类型
/// </summary>
public enum AppleType
{
    None,      // 不吃苹果
    Bronze,    // 铜苹果
    Silver,    // 银苹果
    Gold,      // 金苹果
    Rainbow    // 彩苹果
}

/// <summary>
/// 从者职阶
/// </summary>
public enum ServantClass
{
    Saber,
    Archer,
    Lancer,
    Rider,
    Caster,
    Assassin,
    Berserker,
    Ruler,
    Avenger,
    MoonCancer,
    AlterEgo,
    Foreigner,
    Pretender,
    Beast,
    Shielder,
    All
}

/// <summary>
/// 技能动作
/// </summary>
public class SkillAction
{
    public int Servant { get; set; }   // 0-2: 从者, 3: 御主
    public int Skill { get; set; }     // 0-2
    public int? Target1 { get; set; }
    public int? Target2 { get; set; }  // 换人用

    public override string ToString()
    {
        var servantStr = Servant == 3 ? "Master" : $"S{Servant + 1}";
        var skillStr = $"Skill{Skill + 1}";
        var targetStr = Target1.HasValue ? $" -> {Target1 + 1}" : "";
        if (Target2.HasValue) targetStr += $", {Target2 + 1}";
        return $"{servantStr}.{skillStr}{targetStr}";
    }
}

/// <summary>
/// 回合脚本
/// </summary>
public class TurnScript
{
    public int Turn { get; set; } = 1;
    public int Stage { get; set; } = 1;
    public List<SkillAction> Skills { get; set; } = new();
    public List<int> NoblePhantasms { get; set; } = new();  // 使用宝具的从者索引 (0-2)

    /// <summary>
    /// 从脚本字符串解析
    /// 格式: "1a2b3cjkl" 或 "a1b2c3" 等
    /// </summary>
    public static TurnScript Parse(string script)
    {
        var result = new TurnScript();
        // TODO: 实现脚本解析
        return result;
    }
}

/// <summary>
/// 战斗脚本
/// </summary>
public class BattleScript
{
    public string Name { get; set; } = "";
    public string Description { get; set; } = "";
    public List<TurnScript> Turns { get; set; } = new();

    /// <summary>
    /// 从简化格式解析
    /// 格式: "1:1a2b|2:jkl|3:3c"
    /// </summary>
    public static BattleScript ParseSimple(string name, string script)
    {
        var result = new BattleScript { Name = name };
        // TODO: 实现简化格式解析
        return result;
    }
}

/// <summary>
/// 好友筛选条件
/// </summary>
public class FriendFilter
{
    public string? ServantName { get; set; }
    public ServantClass? Class { get; set; }
    public int? MinSkillLevel { get; set; }
    public string? CraftEssence { get; set; }
    public bool PreferFriend { get; set; } = true;
}

/// <summary>
/// 应用配置
/// </summary>
public class AppConfig
{
    // 通用设置
    public ServerType Server { get; set; } = ServerType.CN;
    public string AdbPath { get; set; } = "adb";
    public string LastDevice { get; set; } = "";

    // 刷本设置
    public AppleType AppleStrategy { get; set; } = AppleType.None;
    public int BattleCount { get; set; } = 1;
    public int TeamIndex { get; set; } = 0;
    public bool AutoFormation { get; set; } = false;
    public bool SkipStory { get; set; } = true;

    // 好友筛选
    public FriendFilter FriendFilter { get; set; } = new();

    // 战斗脚本
    public List<BattleScript> BattleScripts { get; set; } = new();
    public string? CurrentScriptName { get; set; }
}

/// <summary>
/// 配置服务
/// 
/// 管理应用配置，包括战斗脚本、苹果策略、服务器设置等。
/// </summary>
public class ConfigService
{
    private static ConfigService? _instance;
    public static ConfigService Instance => _instance ??= new ConfigService();

    private readonly string _configPath;
    private AppConfig _config = new();

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        Converters = { new JsonStringEnumConverter() }
    };

    public ConfigService()
    {
        _configPath = Path.Combine(AppContext.BaseDirectory, "config", "settings.json");
        Load();
    }

    // ============ 配置属性 ============

    public ServerType Server
    {
        get => _config.Server;
        set { _config.Server = value; Save(); }
    }

    public string AdbPath
    {
        get => _config.AdbPath;
        set { _config.AdbPath = value; Save(); }
    }

    public string LastDevice
    {
        get => _config.LastDevice;
        set { _config.LastDevice = value; Save(); }
    }

    public AppleType AppleStrategy
    {
        get => _config.AppleStrategy;
        set { _config.AppleStrategy = value; Save(); }
    }

    public int BattleCount
    {
        get => _config.BattleCount;
        set { _config.BattleCount = Math.Max(1, value); Save(); }
    }

    public int TeamIndex
    {
        get => _config.TeamIndex;
        set { _config.TeamIndex = Math.Clamp(value, 0, 9); Save(); }
    }

    public bool AutoFormation
    {
        get => _config.AutoFormation;
        set { _config.AutoFormation = value; Save(); }
    }

    public bool SkipStory
    {
        get => _config.SkipStory;
        set { _config.SkipStory = value; Save(); }
    }

    public FriendFilter FriendFilter
    {
        get => _config.FriendFilter;
        set { _config.FriendFilter = value; Save(); }
    }

    public IReadOnlyList<BattleScript> BattleScripts => _config.BattleScripts;

    public BattleScript? CurrentScript
    {
        get => _config.BattleScripts.Find(s => s.Name == _config.CurrentScriptName);
        set { _config.CurrentScriptName = value?.Name; Save(); }
    }

    // ============ 配置操作 ============

    /// <summary>
    /// 加载配置
    /// </summary>
    public void Load()
    {
        try
        {
            if (File.Exists(_configPath))
            {
                var json = File.ReadAllText(_configPath);
                _config = JsonSerializer.Deserialize<AppConfig>(json, JsonOptions) ?? new AppConfig();
                Log.Information("Configuration loaded from {Path}", _configPath);
            }
            else
            {
                _config = new AppConfig();
                CreateDefaultScripts();
                Save();
                Log.Information("Created default configuration");
            }
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Failed to load configuration");
            _config = new AppConfig();
        }
    }

    /// <summary>
    /// 保存配置
    /// </summary>
    public void Save()
    {
        try
        {
            var dir = Path.GetDirectoryName(_configPath);
            if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
            {
                Directory.CreateDirectory(dir);
            }

            var json = JsonSerializer.Serialize(_config, JsonOptions);
            File.WriteAllText(_configPath, json);
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Failed to save configuration");
        }
    }

    /// <summary>
    /// 添加战斗脚本
    /// </summary>
    public void AddBattleScript(BattleScript script)
    {
        // 检查重名
        _config.BattleScripts.RemoveAll(s => s.Name == script.Name);
        _config.BattleScripts.Add(script);
        Save();
    }

    /// <summary>
    /// 删除战斗脚本
    /// </summary>
    public void RemoveBattleScript(string name)
    {
        _config.BattleScripts.RemoveAll(s => s.Name == name);
        if (_config.CurrentScriptName == name)
        {
            _config.CurrentScriptName = null;
        }
        Save();
    }

    /// <summary>
    /// 获取 OCR 模型路径
    /// </summary>
    public string GetOcrModelPath()
    {
        var modelName = Server switch
        {
            ServerType.CN => "zh_cn",
            ServerType.JP => "ja_jp",
            ServerType.NA => "en_us",
            ServerType.TW => "zh_tw",
            _ => "zh_cn"
        };
        return Path.Combine("model", "ocr", modelName);
    }

    /// <summary>
    /// 获取苹果索引（用于 Pipeline 参数）
    /// </summary>
    public int GetAppleIndex()
    {
        return AppleStrategy switch
        {
            AppleType.None => -1,
            AppleType.Bronze => 3,
            AppleType.Silver => 2,
            AppleType.Gold => 1,
            AppleType.Rainbow => 0,
            _ => -1
        };
    }

    private void CreateDefaultScripts()
    {
        // 添加一些默认脚本
        _config.BattleScripts.Add(new BattleScript
        {
            Name = "3T 通用",
            Description = "3回合通用脚本",
            Turns = new List<TurnScript>
            {
                new() { Turn = 1, Stage = 1, Skills = new(), NoblePhantasms = new() { 0 } },
                new() { Turn = 1, Stage = 2, Skills = new(), NoblePhantasms = new() { 1 } },
                new() { Turn = 1, Stage = 3, Skills = new(), NoblePhantasms = new() { 2 } }
            }
        });

        _config.BattleScripts.Add(new BattleScript
        {
            Name = "纯刷本",
            Description = "不使用宝具，智能选卡",
            Turns = new List<TurnScript>()
        });
    }
}
