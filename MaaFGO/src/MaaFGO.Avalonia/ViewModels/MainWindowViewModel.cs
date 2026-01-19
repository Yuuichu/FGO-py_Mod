using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using MaaFGO.Avalonia.Services;
using Serilog;
using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;

namespace MaaFGO.Avalonia.ViewModels;

public partial class MainWindowViewModel : ViewModelBase
{
    private readonly MaaService _maaService;

    public MainWindowViewModel()
    {
        _maaService = MaaService.Instance;
        Tasks = new ObservableCollection<TaskItemViewModel>();
        
        // 添加默认任务
        LoadDefaultTasks();
    }

    // ============ 属性 ============

    [ObservableProperty]
    private string _title = "MaaFGO - Fate/Grand Order 自动化";

    [ObservableProperty]
    private bool _isConnected = false;

    [ObservableProperty]
    private string _connectionStatus = "未连接";

    [ObservableProperty]
    private string _selectedDevice = "";

    [ObservableProperty]
    private bool _isRunning = false;

    [ObservableProperty]
    private string _currentTask = "";

    [ObservableProperty]
    private double _progress = 0;

    [ObservableProperty]
    private string _logText = "";

    [ObservableProperty]
    private ObservableCollection<DeviceInfo> _devices = new();

    [ObservableProperty]
    private ObservableCollection<TaskItemViewModel> _tasks;

    // ============ 命令 ============

    [RelayCommand]
    private async Task RefreshDevicesAsync()
    {
        try
        {
            LogMessage("正在搜索设备...");
            Devices.Clear();

            var deviceList = await _maaService.FindDevicesAsync();
            foreach (var device in deviceList)
            {
                Devices.Add(device);
            }

            LogMessage($"找到 {Devices.Count} 个设备");
        }
        catch (Exception ex)
        {
            LogMessage($"搜索设备失败: {ex.Message}");
            Log.Error(ex, "Failed to refresh devices");
        }
    }

    [RelayCommand]
    private async Task ConnectAsync()
    {
        if (string.IsNullOrEmpty(SelectedDevice))
        {
            LogMessage("请先选择设备");
            return;
        }

        try
        {
            ConnectionStatus = "连接中...";
            LogMessage($"正在连接到 {SelectedDevice}...");

            var success = await _maaService.ConnectAsync(SelectedDevice);

            if (success)
            {
                IsConnected = true;
                ConnectionStatus = "已连接";
                LogMessage("连接成功!");
            }
            else
            {
                ConnectionStatus = "连接失败";
                LogMessage("连接失败，请检查设备状态");
            }
        }
        catch (Exception ex)
        {
            ConnectionStatus = "连接失败";
            LogMessage($"连接出错: {ex.Message}");
            Log.Error(ex, "Failed to connect");
        }
    }

    [RelayCommand]
    private async Task DisconnectAsync()
    {
        try
        {
            await _maaService.DisconnectAsync();
            IsConnected = false;
            ConnectionStatus = "未连接";
            LogMessage("已断开连接");
        }
        catch (Exception ex)
        {
            LogMessage($"断开连接失败: {ex.Message}");
            Log.Error(ex, "Failed to disconnect");
        }
    }

    [RelayCommand]
    private async Task StartAsync()
    {
        if (!IsConnected)
        {
            LogMessage("请先连接设备");
            return;
        }

        try
        {
            IsRunning = true;
            LogMessage("开始执行任务...");

            // 获取选中的任务
            foreach (var task in Tasks)
            {
                if (task.IsEnabled)
                {
                    CurrentTask = task.Name;
                    LogMessage($"执行任务: {task.Name}");

                    var success = await _maaService.RunTaskAsync(task.Entry);

                    if (success)
                    {
                        LogMessage($"任务 {task.Name} 完成");
                    }
                    else
                    {
                        LogMessage($"任务 {task.Name} 失败");
                    }
                }
            }

            LogMessage("所有任务执行完成");
        }
        catch (Exception ex)
        {
            LogMessage($"执行出错: {ex.Message}");
            Log.Error(ex, "Failed to run tasks");
        }
        finally
        {
            IsRunning = false;
            CurrentTask = "";
        }
    }

    [RelayCommand]
    private void Stop()
    {
        try
        {
            _maaService.Stop();
            IsRunning = false;
            LogMessage("已停止任务");
        }
        catch (Exception ex)
        {
            LogMessage($"停止失败: {ex.Message}");
            Log.Error(ex, "Failed to stop");
        }
    }

    // ============ 辅助方法 ============

    private void LoadDefaultTasks()
    {
        Tasks.Add(new TaskItemViewModel { Name = "自动刷本", Entry = "Farming_Start", IsEnabled = true });
        Tasks.Add(new TaskItemViewModel { Name = "友情点召唤", Entry = "FPSummon_Start", IsEnabled = false });
        Tasks.Add(new TaskItemViewModel { Name = "邮箱收取", Entry = "Mail_Start", IsEnabled = false });
        Tasks.Add(new TaskItemViewModel { Name = "抽卡记录", Entry = "SummonHistory_Start", IsEnabled = false });
    }

    private void LogMessage(string message)
    {
        var timestamp = DateTime.Now.ToString("HH:mm:ss");
        LogText += $"[{timestamp}] {message}\n";
        Log.Information(message);
    }
}

/// <summary>
/// 任务项视图模型
/// </summary>
public partial class TaskItemViewModel : ObservableObject
{
    [ObservableProperty]
    private string _name = "";

    [ObservableProperty]
    private string _entry = "";

    [ObservableProperty]
    private bool _isEnabled = false;
}
