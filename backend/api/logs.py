from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from service.logs import log_queue

router = APIRouter(tags=["Logs"])

@router.websocket("/ws/logs")
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
