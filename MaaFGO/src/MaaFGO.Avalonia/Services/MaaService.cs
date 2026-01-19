using MaaFramework.Binding;
using Serilog;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace MaaFGO.Avalonia.Services;

/// <summary>
/// 设备信息
/// </summary>
public class DeviceInfo
{
    public string Name { get; set; } = "";
    public string Address { get; set; } = "";
    public string AdbPath { get; set; } = "";
    public bool IsAdb { get; set; } = true;
    public nint HWnd { get; set; }

    public override string ToString() => $"{Name} ({Address})";
}

/// <summary>
/// MaaFramework 服务
/// 
/// 封装 MaaFramework 的核心功能，提供统一的接口。
/// </summary>
public class MaaService : IDisposable
{
    private static MaaService? _instance;
    public static MaaService Instance => _instance ??= new MaaService();

    private MaaTasker? _tasker;
    private MaaResource? _resource;
    private MaaController? _controller;
    private CancellationTokenSource? _cts;

    private readonly string _resourcePath;

    public MaaService()
    {
        // 资源路径相对于可执行文件
        _resourcePath = Path.Combine(AppContext.BaseDirectory, "..", "..", "resource");
        if (!Directory.Exists(_resourcePath))
        {
            _resourcePath = Path.Combine(AppContext.BaseDirectory, "resource");
        }
    }

    /// <summary>
    /// 查找可用设备
    /// </summary>
    public async Task<List<DeviceInfo>> FindDevicesAsync()
    {
        var devices = new List<DeviceInfo>();

        await Task.Run(() =>
        {
            try
            {
                var toolkit = new MaaToolkit(true);
                var adbDevices = toolkit.AdbDevice.Find();

                foreach (var device in adbDevices)
                {
                    devices.Add(new DeviceInfo
                    {
                        Name = device.Name,
                        Address = device.AdbSerial,
                        AdbPath = device.AdbPath,
                        IsAdb = true
                    });
                }

                Log.Information($"Found {devices.Count} ADB devices");
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to find devices");
            }
        });

        return devices;
    }

    /// <summary>
    /// 连接设备
    /// </summary>
    public async Task<bool> ConnectAsync(string address, string? adbPath = null)
    {
        try
        {
            // 断开现有连接
            await DisconnectAsync();

            // 加载资源
            _resource = new MaaResource();
            var loadStatus = _resource.Post(_resourcePath).Wait();
            if (loadStatus != MaaJobStatus.Succeeded)
            {
                Log.Error("Failed to load resources");
                return false;
            }

            // 创建控制器
            adbPath ??= "adb";
            _controller = new MaaAdbController(
                adbPath,
                address,
                MaaAdbScreencapMethodsEnum.Default,
                MaaAdbInputMethodsEnum.Default,
                "{}"
            );

            // 连接
            var connectStatus = _controller.LinkStart().Wait();
            if (connectStatus != MaaJobStatus.Succeeded)
            {
                Log.Error("Failed to connect to device");
                return false;
            }

            // 创建 Tasker
            _tasker = new MaaTasker();
            _tasker.Bind(_controller, _resource);

            Log.Information($"Connected to device: {address}");
            return true;
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Failed to connect");
            return false;
        }
    }

    /// <summary>
    /// 断开连接
    /// </summary>
    public Task DisconnectAsync()
    {
        return Task.Run(() =>
        {
            try
            {
                _tasker?.Dispose();
                _controller?.Dispose();
                _resource?.Dispose();

                _tasker = null;
                _controller = null;
                _resource = null;

                Log.Information("Disconnected");
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Failed to disconnect");
            }
        });
    }

    /// <summary>
    /// 运行任务
    /// </summary>
    public async Task<bool> RunTaskAsync(string entry, string param = "{}")
    {
        if (_tasker == null)
        {
            Log.Warning("Tasker not initialized");
            return false;
        }

        try
        {
            _cts = new CancellationTokenSource();

            var result = await Task.Run(() =>
            {
                var job = _tasker.Post(entry, param);
                return job.Wait();
            }, _cts.Token);

            return result == MaaJobStatus.Succeeded;
        }
        catch (OperationCanceledException)
        {
            Log.Information("Task cancelled");
            return false;
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Task failed");
            return false;
        }
    }

    /// <summary>
    /// 停止当前任务
    /// </summary>
    public void Stop()
    {
        _cts?.Cancel();
        _tasker?.Abort();
        Log.Information("Task stopped");
    }

    /// <summary>
    /// 截图
    /// </summary>
    public async Task<byte[]?> ScreencapAsync()
    {
        if (_controller == null)
            return null;

        try
        {
            return await Task.Run(() =>
            {
                var status = _controller.Screencap().Wait();
                if (status != MaaJobStatus.Succeeded)
                    return null;

                using var buffer = new MaaImageBuffer();
                if (!_controller.GetCachedImage(buffer))
                    return null;

                return buffer.GetEncodedData().ToArray();
            });
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Screencap failed");
            return null;
        }
    }

    public void Dispose()
    {
        DisconnectAsync().Wait();
    }
}
