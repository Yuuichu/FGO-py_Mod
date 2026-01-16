# 列出所有功能规范
# 用法: .\scripts\list-features.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$SpecsDir = Join-Path $ProjectRoot "specs"

if (-not (Test-Path $SpecsDir)) {
    Write-Host "暂无功能规范" -ForegroundColor Yellow
    exit 0
}

$Features = Get-ChildItem -Path $SpecsDir -Directory

if ($Features.Count -eq 0) {
    Write-Host "暂无功能规范" -ForegroundColor Yellow
    exit 0
}

Write-Host "=== FGO-py 功能规范列表 ===" -ForegroundColor Cyan
Write-Host ""

foreach ($feature in $Features) {
    $specFile = Join-Path $feature.FullName "spec.md"
    $tasksFile = Join-Path $feature.FullName "tasks.md"
    
    $status = "📋 规划中"
    
    if (Test-Path $tasksFile) {
        $tasksContent = Get-Content $tasksFile -Raw
        if ($tasksContent -match '✅') {
            if ($tasksContent -match '⬜|🔄') {
                $status = "🔄 进行中"
            } else {
                $status = "✅ 已完成"
            }
        } elseif ($tasksContent -match '🔄') {
            $status = "🔄 进行中"
        }
    }
    
    Write-Host "  $status $($feature.Name)"
}

Write-Host ""
