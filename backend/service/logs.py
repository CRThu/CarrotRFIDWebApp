import asyncio
import json
from loguru import logger
import sys

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

def setup_logging():
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    logger.add(log_queue, level="DEBUG", serialize=False)
