import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from service.logs import setup_logging
from service.hardware import hw

from api import hardware, command, logs, presets

# 初始化日志
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时不再自动初始化硬件，由前端页面控制连接
    yield
    # 关机清理
    hw.disconnect()

app = FastAPI(lifespan=lifespan, title="CarrotRFID Web API")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(hardware.router)
app.include_router(command.router)
app.include_router(logs.router)
app.include_router(presets.router)

# 挂载前端静态文件 (生产模式)
dist_path = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")
else:
    logger.warning(f"前端构建目录不存在: {dist_path}，请先运行构建脚本。")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=False)
