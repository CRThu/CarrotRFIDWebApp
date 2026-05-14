from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from service.hardware import hw

router = APIRouter(prefix="/api/hardware", tags=["Hardware"])

class ConnectRequest(BaseModel):
    port: str = Field(..., description="串口号")
    baudrate: int = Field(115200, description="波特率")
    reader_type: str = Field("PN532_HSU", description="读卡器类型")

@router.post("/connect")
async def connect_hardware(req: ConnectRequest):
    """连接硬件"""
    success = hw.connect(port=req.port, baudrate=req.baudrate, reader_type=req.reader_type)
    if not success:
        raise HTTPException(status_code=500, detail="连接硬件失败，请检查配置或硬件状态")
    return {"status": "connected"}

@router.post("/disconnect")
async def disconnect_hardware():
    """断开硬件连接"""
    hw.disconnect()
    return {"status": "disconnected"}

@router.get("/status")
async def get_status():
    """获取硬件连接状态"""
    return {
        "connected": hw.reader is not None,
        "port": hw.port,
        "baudrate": hw.baudrate
    }

@router.get("/options")
async def get_options():
    """获取连接选项（可用串口、支持的读卡器）"""
    return {
        "ports": hw.get_available_ports(),
        "readers": hw.get_supported_readers(),
        "baudrates": [9600, 115200, 1000000]
    }

@router.get("/target")
async def get_target():
    """侦测卡片状态"""
    target = hw.get_target()
    return target if target else {"uid": None, "type": "No Target"}

class ConfigRequest(BaseModel):
    tx_crc: bool = True
    rx_crc: bool = True

@router.post("/config")
async def update_config(req: ConfigRequest):
    """更新硬件配置"""
    hw.set_config(req.tx_crc, req.rx_crc)
    return {"status": "ok"}
