import asyncio
import json
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
import sys
import os

# 导入核心库
from crft.drivers.pn532_hsu import PN532_HSU

class LogQueue:
    """日志队列，用于将日志转发至 WebSocket"""
    def __init__(self):
        self.queues = set()

    def add_queue(self, q: asyncio.Queue):
        self.queues.add(q)

    def remove_queue(self, q: asyncio.Queue):
        self.queues.remove(q)

    def __call__(self, message):
        record = message.record
        log_entry = {
            "level": record["level"].name,
            "message": record["message"],
            "timestamp": record["time"].isoformat(),
        }
        for q in self.queues:
            asyncio.create_task(q.put(json.dumps(log_entry)))

log_queue = LogQueue()

# 配置 Loguru
logger.remove()
logger.add(sys.stderr, level="DEBUG")
logger.add(log_queue, level="DEBUG", serialize=False)

class HardwareManager:
    """硬件管理单例"""
    def __init__(self):
        self.reader: Optional[PN532_HSU] = None
        self.lock = asyncio.Lock()

    def init_reader(self, port: str = "COM3"):
        """初始化串口读取器"""
        try:
            logger.info(f"正在初始化 PN532 串口: {port}")
            self.reader = PN532_HSU(port)
            # 简单自检
            self.reader.get_firmware_version()
            logger.info("硬件初始化成功")
        except Exception as e:
            logger.error(f"硬件初始化失败: {e}")
            self.reader = None

hw = HardwareManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化硬件
    # 注意：这里的端口应根据实际情况配置，或通过环境变量传入
    hw.init_reader("COM3") 
    yield
    # 关机清理
    if hw.reader:
        hw.reader.close()

app = FastAPI(lifespan=lifespan, title="CarrotRFID Web API")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/status")
async def get_status():
    """获取硬件连接状态"""
    return {"connected": hw.reader is not None}

from pydantic import BaseModel, Field, field_validator

class Command(BaseModel):
    """指令模型"""
    hex: str = Field(..., description="十六进制指令字符串")

    @field_validator('hex')
    @classmethod
    def validate_hex(cls, v: str) -> str:
        clean_hex = v.replace(" ", "")
        try:
            bytes.fromhex(clean_hex)
        except ValueError:
            raise ValueError("必须是合法的十六进制字符串")
        return clean_hex

@app.post("/api/cmd")
async def send_cmd(cmd: Command):
    """
    接收 Hex 字符串并调用硬件
    """
    if not hw.reader:
        raise HTTPException(status_code=503, detail="硬件未连接")
    
    try:
        raw_data = bytes.fromhex(cmd.hex)
        async with hw.lock:
            logger.info(f"发送指令 [Web]: {cmd.hex}")
            response = hw.reader.raw_command(raw_data)
            return {"response": response.hex().upper() if response else ""}
    except Exception as e:
        logger.error(f"指令执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """日志转发 WebSocket"""
    await websocket.accept()
    q = asyncio.Queue()
    log_queue.add_queue(q)
    try:
        while True:
            log_msg = await q.get()
            await websocket.send_text(log_msg)
    except WebSocketDisconnect:
        pass
    finally:
        log_queue.remove_queue(q)

# 挂载前端静态文件 (生产模式)
dist_path = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")
else:
    logger.warning(f"前端构建目录不存在: {dist_path}，请先运行构建脚本。")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
