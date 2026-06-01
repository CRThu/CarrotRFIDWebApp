# 前端构建脚本
Write-Host "正在构建前端..." -ForegroundColor Cyan

$originalPath = Get-Location
try {
    Set-Location "$PSScriptRoot/frontend"
    bun install
    bun run build
}
finally {
    Set-Location $originalPath
    Write-Host "前端构建完成。" -ForegroundColor Green
}
