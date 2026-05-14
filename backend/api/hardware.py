from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from service.hardware import hw

router = APIRouter(prefix="/api/hardware", tags=["Hardware"])

class ConnectRequest(BaseModel):
    port: str = Field(..., description="串口号")
    baudrate: int = Field(115200, description="波特率")
    reader_type: str = Field("pn532", description="读卡器类型")

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
