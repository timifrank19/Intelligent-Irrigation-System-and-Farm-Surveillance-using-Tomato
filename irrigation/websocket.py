# =============================================================================
# FILE:      irrigation/websocket.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/websocket.py
# PURPOSE:   Single WebSocket connection manager used by the entire app.
#            Handles irrigation, surveillance, tomato, supervisor events.
# =============================================================================

from __future__ import annotations
from typing import List
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict) -> None:
        # Drop dead connections silently; do not hide other errors.
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)
