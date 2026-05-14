from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from service.hardware import hw
from loguru import logger

router = APIRouter(prefix="/api/cmd", tags=["Command"])

class CommandRequest(BaseModel):
    """透传指令模型"""
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

@router.post("/transceive")
async def send_transceive(cmd: CommandRequest):
    """
    接收 Hex 字符串并通过 transceive 发送给卡片
    """
    if not hw.reader:
        raise HTTPException(status_code=503, detail="硬件未连接")
    
    try:
        raw_data = bytes.fromhex(cmd.hex)
        async with hw.lock:
            logger.info(f"发送透传指令 [Web]: {cmd.hex}")
            # 使用 transceive 方法
            response = hw.reader.transceive(raw_data)
            return {"response": response.hex().upper() if response else ""}
    except Exception as e:
        logger.error(f"透传指令执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
