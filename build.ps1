# 前端构建脚本
Write-Host "正在构建前端..." -ForegroundColor Cyan
Push-Location "$PSScriptRoot/frontend"
bun install
bun run build
Pop-Location
Write-Host "前端构建完成。" -ForegroundColor Green
