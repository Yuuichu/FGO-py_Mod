using MaaFramework.Binding;
using Serilog;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace MaaFGO.Avalonia.Services;

/// <summary>
/// 卡牌颜色
/// </summary>
public enum CardColor
{
    Arts,   // 蓝卡
    Quick,  // 绿卡
    Buster  // 红卡
}

/// <summary>
/// 克制类型
/// </summary>
public enum ResistType
{
    Normal,     // 正常
    Effective,  // 克制
    Resist      // 被克
}

/// <summary>
/// 卡牌信息
/// </summary>
public class CardInfo
{
    public CardColor Color { get; set; }
    public int ServantIndex { get; set; }
    public bool IsSealed { get; set; }
    public float CriticalRate { get; set; }
    public ResistType Resist { get; set; }

    /// <summary>
    /// 获取颜色系数
    /// </summary>
    public float ColorCoefficient => Color switch
    {
        CardColor.Arts => 0.8f,
        CardColor.Quick => 1.0f,
        CardColor.Buster => 1.1f,
        _ => 1.0f
    };

    /// <summary>
    /// 获取克制系数
    /// </summary>
    public float ResistCoefficient => Resist switch
    {
        ResistType.Normal => 1.0f,
        ResistType.Effective => 1.7f,
        ResistType.Resist => 0.6f,
        _ => 1.0f
    };
}

/// <summary>
/// 回合信息
/// </summary>
public class TurnInfo
{
    public CardInfo[] Cards { get; set; } = new CardInfo[5];
    public bool[] NoblePhantasmReady { get; set; } = new bool[3];
    public int[] EnemyHP { get; set; } = new int[6];
    public int Stage { get; set; }
    public int StageTotal { get; set; }
}

/// <summary>
/// 战斗状态
/// </summary>
public class BattleState
{
    public int Stage { get; set; } = 1;
    public int StageTotal { get; set; } = 3;
    public int Turn { get; set; } = 0;
    public int StageTurn { get; set; } = 1;

    public int[] ServantHP { get; set; } = new int[3];
    public int[] ServantNP { get; set; } = new int[3];
    public int[][] SkillCooldown { get; set; } = { new int[3], new int[3], new int[3] };
    public int[] MasterSkillCooldown { get; set; } = new int[3];
    public int[] EnemyHP { get; set; } = new int[6];

    /// <summary>
    /// 新回合开始
    /// </summary>
    public void NewTurn(int stage, int stageTotal)
    {
        Turn++;

        if (stage != Stage)
        {
            Stage = stage;
            StageTurn = 1;
        }
        else
        {
            StageTurn++;
        }

        StageTotal = stageTotal;

        // 减少技能冷却
        for (int i = 0; i < 3; i++)
        {
            for (int j = 0; j < 3; j++)
            {
                SkillCooldown[i][j] = Math.Max(0, SkillCooldown[i][j] - 1);
            }
            MasterSkillCooldown[i] = Math.Max(0, MasterSkillCooldown[i] - 1);
        }
    }

    /// <summary>
    /// 使用技能
    /// </summary>
    public void UseSkill(int servant, int skill, int cooldown = 5)
    {
        if (servant >= 0 && servant < 3 && skill >= 0 && skill < 3)
        {
            SkillCooldown[servant][skill] = cooldown;
        }
    }

    /// <summary>
    /// 使用御主技能
    /// </summary>
    public void UseMasterSkill(int skill, int cooldown = 15)
    {
        if (skill >= 0 && skill < 3)
        {
            MasterSkillCooldown[skill] = cooldown;
        }
    }

    /// <summary>
    /// 检查技能是否就绪
    /// </summary>
    public bool IsSkillReady(int servant, int skill)
    {
        return servant >= 0 && servant < 3 && skill >= 0 && skill < 3 
               && SkillCooldown[servant][skill] == 0;
    }

    /// <summary>
    /// 检查御主技能是否就绪
    /// </summary>
    public bool IsMasterSkillReady(int skill)
    {
        return skill >= 0 && skill < 3 && MasterSkillCooldown[skill] == 0;
    }

    /// <summary>
    /// 重置状态（新战斗开始）
    /// </summary>
    public void Reset()
    {
        Stage = 1;
        StageTotal = 3;
        Turn = 0;
        StageTurn = 1;
        ServantHP = new int[3];
        ServantNP = new int[3];
        SkillCooldown = new[] { new int[3], new int[3], new int[3] };
        MasterSkillCooldown = new int[3];
        EnemyHP = new int[6];
    }
}

/// <summary>
/// 战斗服务
/// 
/// 封装战斗逻辑，包括技能释放、选卡策略、宝具使用等。
/// 算法移植自 fgoKernel.ClassicTurn 和 fgoKernel.Turn。
/// </summary>
public class BattleService
{
    private readonly MaaService _maaService;
    private readonly LoggingService _logger;

    public BattleState State { get; } = new();

    // 坐标常量 (1280x720)
    private static readonly (int X, int Y)[] CardPositions = 
    {
        (128, 500), (385, 500), (642, 500), (899, 500), (1156, 500)
    };

    private static readonly (int X, int Y)[] HouguPositions = 
    {
        (318, 250), (640, 250), (962, 250)
    };

    private static readonly (int X, int Y)[][] SkillPositions = 
    {
        new[] { (88, 592), (176, 592), (264, 592) },    // 从者1
        new[] { (406, 592), (494, 592), (582, 592) },   // 从者2
        new[] { (724, 592), (812, 592), (900, 592) }    // 从者3
    };

    private static readonly (int X, int Y)[] TargetPositions = 
    {
        (318, 400), (640, 400), (962, 400)
    };

    private static readonly (int X, int Y) MasterButton = (1200, 340);
    private static readonly (int X, int Y)[] MasterSkillPositions = 
    {
        (1000, 430), (1100, 430), (1200, 430)
    };

    private static readonly (int X, int Y)[] FrontTargets = 
    {
        (200, 360), (400, 360), (600, 360)
    };

    private static readonly (int X, int Y)[] BackTargets = 
    {
        (800, 360), (1000, 360), (1100, 360)
    };

    private static readonly (int X, int Y) ConfirmButton = (640, 550);
    private static readonly (int X, int Y) AttackButton = (1180, 660);

    public BattleService(MaaService maaService)
    {
        _maaService = maaService;
        _logger = LoggingService.Instance;
    }

    /// <summary>
    /// 释放从者技能
    /// </summary>
    public async Task<bool> CastSkillAsync(int servant, int skill, int? target = null)
    {
        if (servant < 0 || servant > 2 || skill < 0 || skill > 2)
        {
            _logger.Warning($"Invalid skill parameters: servant={servant}, skill={skill}");
            return false;
        }

        try
        {
            _logger.Info($"释放技能: 从者{servant + 1} 技能{skill + 1}");

            var pos = SkillPositions[servant][skill];
            await ClickAsync(pos.Item1, pos.Item2);
            await Task.Delay(800);

            if (target.HasValue && target >= 0 && target <= 2)
            {
                var targetPos = TargetPositions[target.Value];
                await ClickAsync(targetPos.Item1, targetPos.Item2);
                await Task.Delay(500);
            }

            State.UseSkill(servant, skill);
            return true;
        }
        catch (Exception ex)
        {
            _logger.Error($"释放技能失败", ex);
            return false;
        }
    }

    /// <summary>
    /// 释放御主技能
    /// </summary>
    public async Task<bool> CastMasterSkillAsync(int skill, int? target1 = null, int? target2 = null)
    {
        if (skill < 0 || skill > 2)
        {
            _logger.Warning($"Invalid master skill: {skill}");
            return false;
        }

        try
        {
            _logger.Info($"释放御主技能: 技能{skill + 1}");

            // 打开御主技能菜单
            await ClickAsync(MasterButton.X, MasterButton.Y);
            await Task.Delay(500);

            // 点击技能
            var pos = MasterSkillPositions[skill];
            await ClickAsync(pos.Item1, pos.Item2);
            await Task.Delay(500);

            // 换人技能特殊处理
            if (skill == 2 && target1.HasValue && target2.HasValue)
            {
                var frontPos = FrontTargets[Math.Clamp(target1.Value, 0, 2)];
                await ClickAsync(frontPos.Item1, frontPos.Item2);
                await Task.Delay(300);

                var backPos = BackTargets[Math.Clamp(target2.Value, 0, 2)];
                await ClickAsync(backPos.Item1, backPos.Item2);
                await Task.Delay(300);

                await ClickAsync(ConfirmButton.X, ConfirmButton.Y);
                await Task.Delay(2500);
            }
            else if (target1.HasValue)
            {
                var targetPos = FrontTargets[Math.Clamp(target1.Value, 0, 2)];
                await ClickAsync(targetPos.Item1, targetPos.Item2);
                await Task.Delay(500);
            }

            State.UseMasterSkill(skill);
            return true;
        }
        catch (Exception ex)
        {
            _logger.Error($"释放御主技能失败", ex);
            return false;
        }
    }

    /// <summary>
    /// 选择卡牌
    /// </summary>
    public async Task<bool> SelectCardsAsync(int[] cardOrder)
    {
        if (cardOrder.Length < 3)
        {
            _logger.Warning("Card order must have at least 3 cards");
            return false;
        }

        try
        {
            // 点击 Attack 按钮
            await ClickAsync(AttackButton.X, AttackButton.Y);
            await Task.Delay(2000);

            // 选择前3张卡
            for (int i = 0; i < 3 && i < cardOrder.Length; i++)
            {
                var cardIndex = Math.Clamp(cardOrder[i], 0, 4);
                var pos = CardPositions[cardIndex];
                await ClickAsync(pos.Item1, pos.Item2);
                await Task.Delay(300);
            }

            _logger.Info($"选卡完成: {string.Join(", ", cardOrder[..Math.Min(3, cardOrder.Length)])}");
            return true;
        }
        catch (Exception ex)
        {
            _logger.Error("选卡失败", ex);
            return false;
        }
    }

    /// <summary>
    /// 使用宝具
    /// </summary>
    public async Task<bool> UseNoblePhantasmAsync(int[] servants)
    {
        if (servants.Length == 0)
            return true;

        try
        {
            // 点击 Attack 按钮
            await ClickAsync(AttackButton.X, AttackButton.Y);
            await Task.Delay(2000);

            // 点击宝具
            foreach (var servant in servants)
            {
                if (servant >= 0 && servant <= 2)
                {
                    var pos = HouguPositions[servant];
                    await ClickAsync(pos.Item1, pos.Item2);
                    await Task.Delay(500);
                    _logger.Info($"使用宝具: 从者{servant + 1}");
                }
            }

            // 补足剩余卡牌
            var cardsNeeded = 3 - servants.Length;
            for (int i = 0; i < cardsNeeded; i++)
            {
                var pos = CardPositions[i];
                await ClickAsync(pos.Item1, pos.Item2);
                await Task.Delay(300);
            }

            return true;
        }
        catch (Exception ex)
        {
            _logger.Error("使用宝具失败", ex);
            return false;
        }
    }

    /// <summary>
    /// 智能选卡（基于卡牌信息）
    /// </summary>
    public async Task<bool> SmartSelectCardsAsync(TurnInfo? turnInfo = null)
    {
        try
        {
            // 如果没有提供回合信息，使用默认顺序
            if (turnInfo?.Cards == null)
            {
                return await SelectCardsAsync(new[] { 0, 1, 2, 3, 4 });
            }

            // 计算最佳卡牌组合
            var bestOrder = CalculateBestCardOrder(turnInfo.Cards);
            return await SelectCardsAsync(bestOrder);
        }
        catch (Exception ex)
        {
            _logger.Error("智能选卡失败", ex);
            return false;
        }
    }

    /// <summary>
    /// 执行战斗脚本
    /// </summary>
    public async Task<bool> ExecuteScriptAsync(TurnScript script)
    {
        try
        {
            // 执行技能
            foreach (var skill in script.Skills)
            {
                if (skill.Servant == 3)
                {
                    // 御主技能
                    await CastMasterSkillAsync(skill.Skill, skill.Target1, skill.Target2);
                }
                else
                {
                    // 从者技能
                    await CastSkillAsync(skill.Servant, skill.Skill, skill.Target1);
                }
                await Task.Delay(500);
            }

            // 使用宝具并选卡
            if (script.NoblePhantasms.Count > 0)
            {
                await UseNoblePhantasmAsync(script.NoblePhantasms.ToArray());
            }
            else
            {
                await SmartSelectCardsAsync();
            }

            return true;
        }
        catch (Exception ex)
        {
            _logger.Error("执行脚本失败", ex);
            return false;
        }
    }

    /// <summary>
    /// 计算最佳卡牌顺序
    /// 移植自 fgoKernel.ClassicTurn 的选卡算法
    /// </summary>
    private int[] CalculateBestCardOrder(CardInfo[] cards)
    {
        if (cards.Length != 5)
            return new[] { 0, 1, 2, 3, 4 };

        var bestScore = float.MinValue;
        int[] bestCombo = { 0, 1, 2 };

        // 遍历所有3卡组合
        for (int i = 0; i < 5; i++)
        {
            for (int j = 0; j < 5; j++)
            {
                if (j == i) continue;
                for (int k = 0; k < 5; k++)
                {
                    if (k == i || k == j) continue;

                    var combo = new[] { i, j, k };
                    var score = EvaluateCombo(cards, combo);

                    if (score > bestScore)
                    {
                        bestScore = score;
                        bestCombo = combo;
                    }
                }
            }
        }

        // 补全剩余卡牌
        var result = new List<int>(bestCombo);
        for (int i = 0; i < 5; i++)
        {
            if (!result.Contains(i))
                result.Add(i);
        }

        return result.ToArray();
    }

    /// <summary>
    /// 评估卡牌组合得分
    /// </summary>
    private float EvaluateCombo(CardInfo[] cards, int[] combo)
    {
        // 检查封印
        if (cards[combo[0]].IsSealed || cards[combo[1]].IsSealed || cards[combo[2]].IsSealed)
            return float.MinValue;

        // 颜色链检测
        bool isColorChain = cards[combo[0]].Color == cards[combo[1]].Color 
                         && cards[combo[1]].Color == cards[combo[2]].Color;

        // 首卡加成 (红卡首位 +0.3)
        float firstCardBonus = cards[combo[0]].Color == CardColor.Buster ? 0.3f : 0f;

        // 位置系数
        float[] posBonus = { 1.0f, 1.2f, 1.4f };

        // 基础伤害
        float baseDamage = 0f;
        for (int i = 0; i < 3; i++)
        {
            var card = cards[combo[i]];
            baseDamage += (firstCardBonus + posBonus[i] * card.ColorCoefficient) 
                        * (1 + card.CriticalRate) 
                        * card.ResistCoefficient;
        }

        // 链加成
        float chainBonus = 0f;
        if (isColorChain)
        {
            chainBonus = 4.8f;
        }

        // 同从者链加成 (Brave Chain)
        bool isBraveChain = cards[combo[0]].ServantIndex == cards[combo[1]].ServantIndex
                         && cards[combo[1]].ServantIndex == cards[combo[2]].ServantIndex;
        if (isBraveChain)
        {
            chainBonus += (firstCardBonus + 1.0f) * (isColorChain ? 3f : 1.8f) 
                        * cards[combo[0]].ResistCoefficient;
        }

        return baseDamage + chainBonus;
    }

    private async Task ClickAsync(int x, int y)
    {
        // TODO: 通过 MaaService 执行点击
        // 目前 MaaService 没有暴露直接点击接口，需要扩展
        await Task.Delay(100);
    }
}
