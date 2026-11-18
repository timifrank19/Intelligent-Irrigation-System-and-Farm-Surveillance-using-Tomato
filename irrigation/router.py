# =============================================================================
# FILE:      irrigation/router.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/router.py
# PURPOSE:   Aggregates all irrigation routes into one APIRouter plus the
#            shared WebSocket endpoint. Mounted by irrigation_backend.py.
# =============================================================================

from __future__ import annotations
from fastapi import APIRouter, WebSocket

from .websocket import websocket_endpoint
from .routes import sensors, status, thresholds, forecast, override, admin, pages

irrigation_router = APIRouter()
irrigation_router.include_router(sensors.router)
irrigation_router.include_router(status.router)
irrigation_router.include_router(thresholds.router)
irrigation_router.include_router(forecast.router)
irrigation_router.include_router(override.router)
irrigation_router.include_router(admin.router)
irrigation_router.include_router(pages.router)


# WebSocket is registered by the main app; expose the handler for mounting.
def register_websocket(app):
    @app.websocket("/ws")
    async def _ws(ws: WebSocket):
        await websocket_endpoint(ws)
