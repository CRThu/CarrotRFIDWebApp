# CarrotRFIDWebApp

Sidecar 可视化控制台，用于监控和调试 CarrotRFID 硬件。

## 技术栈
- **后端**: Python 3.14 + FastAPI + UV
- **前端**: Vue 3 + TypeScript + Bun + Vite + TailwindCSS

## 快速开始

### 开发模式 (推荐)
一键启动前端和后端开发服务器：
```powershell
.\dev.ps1
```
- 界面访问: `http://localhost:3000`
- API 地址: `http://localhost:8000`

### 生产模式 (后端托管前端)
1. 构建前端：
   ```powershell
   .\build.ps1
   ```
2. 启动服务：
   ```powershell
   .\run.ps1
   ```
- 访问地址: `http://localhost:8000`
