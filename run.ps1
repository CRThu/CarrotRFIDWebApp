# 运行脚本 (后端带起前端)
Write-Host "正在启动 CarrotRFID Web App..." -ForegroundColor Cyan
Push-Location "$PSScriptRoot/backend"
uv run uvicorn main:app --host 0.0.0.0 --port 8000
Pop-Location
