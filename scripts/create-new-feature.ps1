# 创建新功能规范目录 (Windows PowerShell 版本)
# 用法: .\scripts\create-new-feature.ps1 <feature-name>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$FeatureName
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$FeatureDir = Join-Path $ProjectRoot "specs" $FeatureName

if (Test-Path $FeatureDir) {
    Write-Error "错误: 功能目录已存在: $FeatureDir"
    exit 1
}

Write-Host "创建功能目录: $FeatureDir"
New-Item -ItemType Directory -Path $FeatureDir -Force | Out-Null

# 复制模板
$TemplatesDir = Join-Path $ProjectRoot "templates"

Copy-Item (Join-Path $TemplatesDir "spec-template.md") (Join-Path $FeatureDir "spec.md")
Copy-Item (Join-Path $TemplatesDir "plan-template.md") (Join-Path $FeatureDir "plan.md")
Copy-Item (Join-Path $TemplatesDir "tasks-template.md") (Join-Path $FeatureDir "tasks.md")

# 替换模板中的占位符
$files = @("spec.md", "plan.md", "tasks.md")
foreach ($file in $files) {
    $filePath = Join-Path $FeatureDir $file
    $content = Get-Content $filePath -Raw -Encoding UTF8
    $content = $content -replace '\[功能名称\]', $FeatureName
    Set-Content $filePath -Value $content -Encoding UTF8
}

Write-Host "✅ 功能规范目录已创建" -ForegroundColor Green
Write-Host ""
Write-Host "下一步:"
Write-Host "  1. 编辑 specs/$FeatureName/spec.md 定义功能需求"
Write-Host "  2. 编辑 specs/$FeatureName/plan.md 制定实现计划"
Write-Host "  3. 编辑 specs/$FeatureName/tasks.md 分解具体任务"
