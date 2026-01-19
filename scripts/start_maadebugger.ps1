# MaaDebugger 启动脚本
Write-Host "Starting MaaDebugger..." -ForegroundColor Green
Write-Host ""
Write-Host "MaaDebugger will open in your browser at http://localhost:8080" -ForegroundColor Cyan
Write-Host ""

python -m MaaDebugger --port 8080
