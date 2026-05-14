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
    - `logs.py`: 日志队列管道，集成 `loguru` 并接入 `crft.trace.manager` 实现层级化日志（DRIVER/PROTOCOL）转发。
- **动态控制**:
  - 不在 `lifespan` 内硬编码连接逻辑，完全由客户端发起 `connect` 控制，支持从前端自由选择波特率和读卡器。

### 前端 (Frontend Implementation)
- **响应式状态**:
  - `logs`: 响应式数组，存储最近 1000 条日志。
  - `history`: 记录已发送的高层指令及响应。
  - `txCrc`, `rxCrc`: 独立控制发送与接收的 CRC 校验。
- **实时通信**:
  - `checkStatus()`: 每 3 秒轮询同步。
  - `fetchTarget()`: 侦测卡片 UID 和 SAK。支持手动 SCAN 和 AUTO 轮询模式。
- **UI 布局**:
  - **Workbench Layout**: 三栏式工作台设计。
  - **Control Panel**: 包含硬件配置、串口刷新按钮及卡片上下文侦测。
  - **Instruction Commander**: 提供 NTAG 等高层协议指令库，支持指令注入与透传调试。
  - **Monitor**: 日志与历史记录，支持对 `DRIVER` 和 `PROTOCOL` 层级进行实时过滤和颜色高亮。

---

## API 接口参考 (API Reference)

### 硬件控制 (Hardware)
- `GET /api/hardware/options`: 获取可用串口、读卡器及波特率。
  - **返回**: `{"ports": ["COM1", ...], "readers": ["PN532_HSU"], "baudrates": [9600, ...]}`
- `GET /api/hardware/status`: 获取当前硬件连接状态。
  - **返回**: `{"connected": true, "port": "COM3", "baudrate": 115200}`
- `GET /api/hardware/target`: 侦测当前场内卡片信息。
  - **返回**: `{"uid": "04A1B2C3", "sak": "0x08", "type": "Mifare Classic 1K"}`
- `POST /api/hardware/connect`: 连接硬件设备。
  - **请求体**: `{"port": "COM3", "baudrate": 115200, "reader_type": "PN532_HSU"}`
- `POST /api/hardware/disconnect`: 断开硬件连接。
- `POST /api/hardware/config`: 更新硬件参数（独立控制 TX/RX CRC）。
  - **请求体**: `{"tx_crc": true, "rx_crc": true}`

### 指令透传 (Command)
- `POST /api/cmd/transceive`: 发送高层协议指令（Raw Card Command）。
  - **请求体**: `{"hex": "30 04"}` (不再需要 PN532 帧封装)
  - **返回**: `{"response": "A1 B2 C3 ..."}`

### 指令预设 (Presets)
- `GET /api/presets`: 获取所有卡种分类列表。
  - **返回**: `["NTAG", ...]`
- `GET /api/presets/{category}`: 获取指定分类下的指令模版。
  - **返回**: `[{"name": "...", "hex": "...", "desc": "..."}]`

### 日志流 (Logs)
- `WS /ws/logs`: 建立 WebSocket 连接接收实时日志流。
  - **消息格式**: `{"level": "INFO|WARN|ERROR|DEBUG|DRIVER|PROTOCOL", "message": "...", "timestamp": "..."}`
  - **注意**: `WARNING` 级别会自动映射为 `WARN` 以兼容前端。

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
4. **日志规范**: 接入 `crft.trace` 架构，核心驱动和协议层日志应分别标记为 `DRIVER` 和 `PROTOCOL` 级别，前端通过过滤开关控制显示。
