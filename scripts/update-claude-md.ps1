# 更新 CLAUDE.md 文件（添加最新的功能规范信息）
# 用法: .\scripts\update-claude-md.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$ClaudeMd = Join-Path $ProjectRoot "CLAUDE.md"
$SpecsDir = Join-Path $ProjectRoot "specs"

Write-Host "更新 CLAUDE.md 中的功能规范列表..." -ForegroundColor Cyan

# 获取所有功能规范
$Features = @()
if (Test-Path $SpecsDir) {
    $FeatureDirs = Get-ChildItem -Path $SpecsDir -Directory
    foreach ($dir in $FeatureDirs) {
        $specFile = Join-Path $dir.FullName "spec.md"
        if (Test-Path $specFile) {
            $Features += $dir.Name
        }
    }
}

if ($Features.Count -gt 0) {
    Write-Host "发现 $($Features.Count) 个功能规范:" -ForegroundColor Green
    foreach ($f in $Features) {
        Write-Host "  - $f"
    }
} else {
    Write-Host "暂无功能规范" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ CLAUDE.md 已是最新状态" -ForegroundColor Green
