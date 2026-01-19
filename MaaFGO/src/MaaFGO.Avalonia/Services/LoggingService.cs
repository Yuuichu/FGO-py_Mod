using Serilog;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace MaaFGO.Avalonia.Services;

/// <summary>
/// 日志级别
/// </summary>
public enum LogLevel
{
    Debug,
    Info,
    Warning,
    Error
}

/// <summary>
/// 日志条目
/// </summary>
public class LogEntry
{
    public DateTime Timestamp { get; set; }
    public LogLevel Level { get; set; }
    public string Message { get; set; } = "";

    public override string ToString()
    {
        var levelStr = Level switch
        {
            LogLevel.Debug => "DEBUG",
            LogLevel.Info => "INFO",
            LogLevel.Warning => "WARN",
            LogLevel.Error => "ERROR",
            _ => "INFO"
        };
        return $"[{Timestamp:HH:mm:ss}] [{levelStr}] {Message}";
    }
}

/// <summary>
/// 日志服务
/// 
/// 提供统一的日志管理，同时支持 Serilog 后端和 UI 显示。
/// </summary>
public class LoggingService
{
    private static LoggingService? _instance;
    public static LoggingService Instance => _instance ??= new LoggingService();

    private readonly List<LogEntry> _logs = new();
    private readonly object _lock = new();

    /// <summary>
    /// 日志添加事件（用于 UI 绑定）
    /// </summary>
    public event Action<LogEntry>? OnLogAdded;

    /// <summary>
    /// 最大日志条数
    /// </summary>
    public int MaxLogCount { get; set; } = 1000;

    /// <summary>
    /// 日志历史（只读）
    /// </summary>
    public IReadOnlyList<LogEntry> Logs
    {
        get
        {
            lock (_lock)
            {
                return new ReadOnlyCollection<LogEntry>(_logs);
            }
        }
    }

    /// <summary>
    /// 记录调试日志
    /// </summary>
    public void Debug(string message)
    {
        AddLog(LogLevel.Debug, message);
        Log.Debug(message);
    }

    /// <summary>
    /// 记录信息日志
    /// </summary>
    public void Info(string message)
    {
        AddLog(LogLevel.Info, message);
        Log.Information(message);
    }

    /// <summary>
    /// 记录警告日志
    /// </summary>
    public void Warning(string message)
    {
        AddLog(LogLevel.Warning, message);
        Log.Warning(message);
    }

    /// <summary>
    /// 记录错误日志
    /// </summary>
    public void Error(string message, Exception? ex = null)
    {
        AddLog(LogLevel.Error, message);
        if (ex != null)
        {
            Log.Error(ex, message);
        }
        else
        {
            Log.Error(message);
        }
    }

    /// <summary>
    /// 清空日志
    /// </summary>
    public void Clear()
    {
        lock (_lock)
        {
            _logs.Clear();
        }
    }

    /// <summary>
    /// 获取格式化的日志文本
    /// </summary>
    public string GetFormattedLogs()
    {
        lock (_lock)
        {
            return string.Join("\n", _logs);
        }
    }

    private void AddLog(LogLevel level, string message)
    {
        var entry = new LogEntry
        {
            Timestamp = DateTime.Now,
            Level = level,
            Message = message
        };

        lock (_lock)
        {
            _logs.Add(entry);

            // 限制日志数量
            while (_logs.Count > MaxLogCount)
            {
                _logs.RemoveAt(0);
            }
        }

        // 触发事件（UI 线程需要自行处理调度）
        OnLogAdded?.Invoke(entry);
    }
}
