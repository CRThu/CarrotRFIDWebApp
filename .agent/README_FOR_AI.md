# CarrotRFIDWebApp (Sidecar Console)

## 项目概述
本仓库是 `CarrotRFIDTester` 的**旁路可视化 Web 控制台**。它通过本地依赖引用主仓库库，提供硬件连接监控、工业级实时日志流可视化以及十六进制指令调试功能。

## 技术栈选型及理由

### 1. 后端: FastAPI (Python)
- **异步性能**: 基于 `AnyIO`，完美支撑 WebSocket (日志流) 与 HTTP (指令控制) 并行处理。
- **类型安全**: 引入 `Pydantic` 进行指令校验。
- **包管理**: 使用 `uv`。项目名为 `carrotrfidwebapp`，要求 Python >= 3.14。

### 2. 前端: Vue 3 + TypeScript + Tailwind CSS + DaisyUI
- **TypeScript**: 增强类型安全，特别是处理复杂的十六进制指令交互。
- **Vue 3 (Composition API)**: 提供响应式逻辑。
- **Tailwind CSS & DaisyUI**: 极速构建现代 UI。
- **包管理**: 使用 `bun`，负责依赖安装、构建及开发服务器运行。

---

## 代码实现概要 (Implementation Summary)

### 后端 (Backend Implementation)
- **架构分层**:
  - **`api` 层**: 提供 RESTful 端点和 WebSocket 服务。
    - `hardware.py`: 提供 `/api/hardware/connect`, `/api/hardware/disconnect`, `/api/hardware/status`，支持动态选择物理信道与波特率。
    - `command.py`: 提供 `/api/cmd/transceive` 接收透传指令，通过调用 `PN532_HSU` 的 `transceive` 实现标准透传。
    - `logs.py`: 提供 `/ws/logs` 实时日志推送。
  - **`service` 层**: 核心业务与硬件控制。
    - `hardware.py`: `HardwareManager` 硬件管理单例，控制 `SerialTransport` 与 `PN532_HSU` 的生命周期，确保 Web 端并发指令时的原子性。
    - `logs.py`: 日志队列管道，集成 loguru 转发前端。
- **动态控制**:
  - 不在 `lifespan` 内硬编码连接逻辑，完全由客户端发起 `connect` 控制，支持从前端自由选择波特率和读卡器。

### 前端 (Frontend Implementation)
- **响应式状态**:
  - `logs`: 响应式数组，存储最近 500 条日志，超限自动 `shift`。
  - `activeFilters`: 日志级别动态过滤数组。
- **实时通信**:
  - `connectWS()`: 实现 WebSocket 自动重连机制（2秒间隔）。
  - `checkStatus()`: 每 5 秒轮询后端同步硬件连接状态。
- **UI 布局**:
  - **Header**: 包含动态渐变标题和连接状态 Stats 指示器。
  - **Console**: 采用 `mockup-code` 风格，各级别日志（DEBUG/INFO/WARN/ERROR）通过 Tailwind 类实现不同配色。
  - **Command**: 组合式输入框，支持 `Enter` 快捷发送。

---

## 运行指南

### 后端 (Python/uv)
```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

### 前端 (Vue/bun)
```bash
cd frontend
bun install
bun run dev --port 3000
```

---

## AI 协助开发准则
1. **指令安全**: 新增任何硬件交互接口，必须使用 Pydantic 进行输入验证。
2. **UI 规范**: 优先使用 DaisyUI 现成组件，保持深色模式风格一致（`data-theme="dark"`）。
3. **隔离性**: 严禁在本项目中修改 `../../CarrotRFIDTester` 目录下的代码，所有逻辑应在 `backend/main.py` 中通过核心库 API 实现。
4. **日志规范**: 前端根据日志内容中的 `[Web]` 标签可识别出哪些操作源自 Web 端。
