# 开发运行脚本 (前端后端独立运行)
Write-Host "正在并行启动前端和后端开发服务器..." -ForegroundColor Cyan

# 启动后端
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'CarrotRFID Backend'; Set-Location '$PSScriptRoot/backend'; uv run uvicorn main:app --reload"

# 启动前端
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle = 'CarrotRFID Frontend'; Set-Location '$PSScriptRoot/frontend'; bun run dev"

Write-Host "开发服务器已启动。" -ForegroundColor Green
