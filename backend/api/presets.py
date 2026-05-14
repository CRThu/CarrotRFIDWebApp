from fastapi import APIRouter
from typing import List, Dict

router = APIRouter(prefix="/api/presets", tags=["Presets"])

# 高层协议指令库（基于卡片指令集，不含 PN532 帧头帧尾）
PRESETS = {
    "NTAG": [
        {"name": "GET_VERSION", "hex": "60", "desc": "获取 NTAG 版本信息"},
        {"name": "READ Page 4", "hex": "30 04", "desc": "读取第 4 页及后续 3 页"},
        {"name": "FAST_READ 4-7", "hex": "3A 04 07", "desc": "快速读取第 4 到 7 页"},
        {"name": "WRITE Page 4", "hex": "A2 04 00 00 00 00", "desc": "向第 4 页写入 4 字节数据"},
        {"name": "READ_SIG", "hex": "3C 00", "desc": "读取卡片 ECC 签名"},
    ]
}

@router.get("")
async def get_categories():
    """获取指令库分类"""
    return list(PRESETS.keys())

@router.get("/{category}")
async def get_presets(category: str):
    """获取指定分类下的指令"""
    return PRESETS.get(category, [])
