using Serilog;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace MaaFGO.Avalonia.Services;

/// <summary>
/// 好友信息
/// </summary>
public class FriendInfo
{
    public string ServantName { get; set; } = "";
    public ServantClass Class { get; set; }
    public int Level { get; set; }
    public int[] SkillLevels { get; set; } = new int[3];
    public string CraftEssence { get; set; } = "";
    public bool IsFriend { get; set; }
    public int Position { get; set; }  // 列表位置 (0-6)

    /// <summary>
    /// 获取技能等级字符串
    /// </summary>
    public string SkillLevelString => $"{SkillLevels[0]}/{SkillLevels[1]}/{SkillLevels[2]}";

    /// <summary>
    /// 检查是否匹配筛选条件
    /// </summary>
    public bool Matches(FriendFilter filter)
    {
        if (filter.Class.HasValue && filter.Class != Class)
            return false;

        if (!string.IsNullOrEmpty(filter.ServantName) && 
            !ServantName.Contains(filter.ServantName, StringComparison.OrdinalIgnoreCase))
            return false;

        if (filter.MinSkillLevel.HasValue)
        {
            var minSkill = Math.Min(SkillLevels[0], Math.Min(SkillLevels[1], SkillLevels[2]));
            if (minSkill < filter.MinSkillLevel)
                return false;
        }

        if (!string.IsNullOrEmpty(filter.CraftEssence) &&
            !CraftEssence.Contains(filter.CraftEssence, StringComparison.OrdinalIgnoreCase))
            return false;

        if (filter.PreferFriend && !IsFriend)
            return false;

        return true;
    }
}

/// <summary>
/// 好友服务
/// 
/// 管理好友助战选择逻辑。
/// </summary>
public class FriendService
{
    private readonly MaaService _maaService;
    private readonly ConfigService _configService;
    private readonly LoggingService _logger;

    // 好友列表位置 (1280x720)
    private static readonly (int X, int Y)[] FriendPositions =
    {
        (640, 180),  // 位置1
        (640, 300),  // 位置2
        (640, 420),  // 位置3
        (640, 540),  // 位置4
    };

    private static readonly (int X, int Y) RefreshButton = (1200, 130);
    private static readonly (int X, int Y) RefreshConfirm = (640, 560);
    private static readonly (int X, int Y) ScrollStart = (640, 550);
    private static readonly (int X, int Y) ScrollEnd = (640, 200);

    public FriendService(MaaService maaService)
    {
        _maaService = maaService;
        _configService = ConfigService.Instance;
        _logger = LoggingService.Instance;
    }

    /// <summary>
    /// 选择好友助战
    /// </summary>
    public async Task<bool> SelectFriendAsync(FriendFilter? filter = null)
    {
        filter ??= _configService.FriendFilter;

        try
        {
            _logger.Info("开始选择好友助战...");

            // 尝试在当前列表中查找
            var friends = await DetectFriendsAsync();
            var match = FindMatchingFriend(friends, filter);

            if (match != null)
            {
                return await ClickFriendAsync(match.Position);
            }

            // 未找到匹配，尝试滚动查找
            for (int scroll = 0; scroll < 5; scroll++)
            {
                await ScrollFriendListAsync();
                await Task.Delay(1000);

                friends = await DetectFriendsAsync();
                match = FindMatchingFriend(friends, filter);

                if (match != null)
                {
                    return await ClickFriendAsync(match.Position);
                }
            }

            // 仍未找到，尝试刷新列表
            _logger.Info("未找到匹配好友，尝试刷新列表...");
            if (await RefreshFriendListAsync())
            {
                await Task.Delay(2000);

                friends = await DetectFriendsAsync();
                match = FindMatchingFriend(friends, filter);

                if (match != null)
                {
                    return await ClickFriendAsync(match.Position);
                }
            }

            // 最后降级：选择第一个好友
            _logger.Warning("未找到匹配好友，选择第一个助战");
            return await ClickFriendAsync(0);
        }
        catch (Exception ex)
        {
            _logger.Error("选择好友失败", ex);
            return false;
        }
    }

    /// <summary>
    /// 刷新好友列表
    /// </summary>
    public async Task<bool> RefreshFriendListAsync()
    {
        try
        {
            _logger.Info("刷新好友列表...");

            // 点击刷新按钮
            await ClickAsync(RefreshButton.X, RefreshButton.Y);
            await Task.Delay(500);

            // 确认刷新
            await ClickAsync(RefreshConfirm.X, RefreshConfirm.Y);
            await Task.Delay(10000);  // 等待刷新冷却

            return true;
        }
        catch (Exception ex)
        {
            _logger.Error("刷新好友列表失败", ex);
            return false;
        }
    }

    /// <summary>
    /// 检测当前可见的好友列表
    /// </summary>
    public async Task<List<FriendInfo>> DetectFriendsAsync()
    {
        var friends = new List<FriendInfo>();

        try
        {
            // TODO: 实现基于 OCR 的好友信息识别
            // 需要使用 MaaService 进行截图和 OCR

            // 暂时返回模拟数据
            for (int i = 0; i < 4; i++)
            {
                friends.Add(new FriendInfo
                {
                    Position = i,
                    ServantName = $"助战从者{i + 1}",
                    Class = ServantClass.All,
                    Level = 90,
                    SkillLevels = new[] { 10, 10, 10 },
                    IsFriend = i < 2
                });
            }
        }
        catch (Exception ex)
        {
            _logger.Error("检测好友列表失败", ex);
        }

        return friends;
    }

    /// <summary>
    /// 查找匹配的好友
    /// </summary>
    public FriendInfo? FindMatchingFriend(List<FriendInfo> friends, FriendFilter filter)
    {
        // 优先查找好友
        if (filter.PreferFriend)
        {
            foreach (var friend in friends)
            {
                if (friend.IsFriend && friend.Matches(filter))
                    return friend;
            }
        }

        // 查找所有匹配
        foreach (var friend in friends)
        {
            if (friend.Matches(filter))
                return friend;
        }

        return null;
    }

    /// <summary>
    /// 滚动好友列表
    /// </summary>
    private async Task ScrollFriendListAsync()
    {
        // TODO: 通过 MaaService 执行滑动
        await Task.Delay(500);
    }

    /// <summary>
    /// 点击选择好友
    /// </summary>
    private async Task<bool> ClickFriendAsync(int position)
    {
        if (position < 0 || position >= FriendPositions.Length)
        {
            _logger.Warning($"Invalid friend position: {position}");
            return false;
        }

        var pos = FriendPositions[position];
        await ClickAsync(pos.X, pos.Y);
        await Task.Delay(500);

        _logger.Info($"选择好友: 位置 {position + 1}");
        return true;
    }

    private async Task ClickAsync(int x, int y)
    {
        // TODO: 通过 MaaService 执行点击
        await Task.Delay(100);
    }
}
