import asyncio
import json
import sys
from loguru import logger
from nfctester.trace.manager import trace

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
        level = record["level"].name
        
        # 映射 WARNING 为 WARN，兼容前端过滤器
        if level == "WARNING":
            level = "WARN"
            
        # 提取层级信息 (DRIVER/PROTOCOL)
        layer = record["extra"].get("layer")
        
        log_entry = {
            "level": layer if layer else level,
            "message": record["message"],
            "timestamp": record["time"].isoformat(),
        }
        for q in self.queues:
            asyncio.create_task(q.put(json.dumps(log_entry)))

log_queue = LogQueue()

def setup_logging():
    # 使用 trace 管理器统一配置，避免重复调用 logger.remove() 冲突
    # trace.set_level 会调用 _reconfigure()，其中包含 logger.remove()
    trace.set_level("DEBUG")
    
    # 在 trace 配置的基础上，添加 WebSocket 转发队列
    # 使用 trace._filter 以确保层级开关（DRIVER/PROTOCOL）生效
    logger.add(log_queue, level="TRACE", filter=trace._filter, serialize=False)
    
    # 默认开启详细追踪（可选，根据用户需求）
    trace.set_layer("DRIVER", True)
    trace.set_layer("PROTOCOL", True)
