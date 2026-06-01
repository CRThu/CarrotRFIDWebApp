import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from service.hardware import hw
from loguru import logger

router = APIRouter(prefix="/api/cmd", tags=["Command"])

# 位标记正则：匹配 N'hXX 格式（如 7'h26, 4'hC）
BIT_PATTERN = re.compile(r'(\d+)\s*\'h\s*([0-9a-fA-F]+)')


def parse_bit_notation(text: str) -> tuple[str, int]:
    """
    解析包含位标记的输入文本，返回 (clean_hex, tx_last_bits)
    例如:
      "AA BB 7'h26" -> ("AABB26", 7)
      "AABB 7'h26"  -> ("AABB26", 7)
      "7'h26"       -> ("26", 7)
      "AA BB CC"    -> ("AABBCC", 0)
    """
    tx_last_bits = 0
    cleaned = text.strip()

    matches = list(BIT_PATTERN.finditer(cleaned))
    if matches:
        last_match = matches[-1]
        tx_last_bits = int(last_match.group(1))
        if tx_last_bits < 1 or tx_last_bits > 7:
            raise ValueError(f"last bits 必须为 1-7，接收到: {tx_last_bits}")
        hex_val = last_match.group(2)
        # 将位标记替换为纯十六进制值
        cleaned = cleaned[:last_match.start()] + hex_val + cleaned[last_match.end():]

    clean_hex = cleaned.replace(" ", "")
    if clean_hex:
        try:
            bytes.fromhex(clean_hex)
        except ValueError:
            raise ValueError(f"解析后的十六进制不合法: {clean_hex}")

    return clean_hex, tx_last_bits


def format_response_with_bits(hex_str: str, last_bits: int) -> str:
    """
    将响应格式化为带位标记的字符串
    例如:
      ("AABB26", 7) -> "AA BB 7'h26"
      ("AABB26", 4) -> "AA BB 4'h6"
      ("AABBCC", 0) -> "AA BB CC"
    """
    if not hex_str:
        return ""

    if last_bits == 0:
        # 纯十六进制，每两个字符一组
        return ' '.join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))

    # 有 last_bits，将最后一个字节用位标记表示
    last_byte = hex_str[-2:] if len(hex_str) >= 2 else hex_str
    prefix = hex_str[:-2]

    if prefix:
        formatted_prefix = ' '.join(prefix[i:i+2] for i in range(0, len(prefix), 2))
        return f"{formatted_prefix} {last_bits}'h{last_byte.upper()}"
    else:
        return f"{last_bits}'h{last_byte.upper()}"


class CommandRequest(BaseModel):
    """透传指令模型"""
    hex: str = Field(..., description="十六进制指令字符串（支持 N'hXX 位标记格式）")
    tx_last_bits: int = Field(0, description="最后发送字节的有效位数（0表示整字节），旧格式兼容")

    @field_validator('hex')
    @classmethod
    def validate_hex(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("指令不能为空")

        # 如果包含位标记，用 parse_bit_notation 校验
        if "'h" in v.lower():
            try:
                parse_bit_notation(v)
            except ValueError as e:
                raise ValueError(str(e))
            return v  # 保留原始格式让 endpoint 解析

        # 传统格式：直接校验十六进制
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
    支持 N'hXX 位标记格式（如 AA BB 7'h26, AABB 7'h26, 7'h26）
    """
    if not hw.reader:
        raise HTTPException(status_code=503, detail="硬件未连接")

    try:
        # 解析输入：提取位标记和十六进制数据
        clean_hex, tx_last_bits = parse_bit_notation(cmd.hex)

        # 如果传统格式提供了 tx_last_bits 且没有位标记，使用传统值
        if tx_last_bits == 0 and cmd.tx_last_bits > 0:
            tx_last_bits = cmd.tx_last_bits

        raw_data = bytes.fromhex(clean_hex)
        async with hw.lock:
            logger.info(f"发送透传指令 [Web]: {clean_hex}, TxBits: {tx_last_bits}")
            response, rx_last_bits = hw.transceive(raw_data, tx_last_bits)

            resp_hex = response.hex().upper() if response else ""
            formatted_resp = format_response_with_bits(resp_hex, rx_last_bits)

            return {
                "response": resp_hex,
                "response_formatted": formatted_resp,
                "rx_last_bits": rx_last_bits,
                "tx_hex_sent": clean_hex,
                "tx_last_bits": tx_last_bits
            }
    except ValueError as e:
        logger.error(f"指令解析失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"透传指令执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
