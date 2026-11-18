# =============================================================================
# FILE:      irrigation/routes/override.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/routes/override.py
# PURPOSE:   GET /api/manual-override/toggle — admin-gated manual pump control.
# =============================================================================

from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Request

from .. import config as cfg
from .. import state
from ..websocket import manager

router = APIRouter()


@router.get("/api/manual-override/toggle")
async def toggle_manual_override(request: Request):
    password = request.query_params.get("password", "")
    user_ip = request.client.host if request.client else "unknown"

    if password != cfg.ADMIN_PASSWORD:
        return {"error": "Admin password required", "authorized": False}

    if state.admin_lock and state.admin_lock_user != user_ip:
        if state.admin_lock_time and \
           (datetime.now() - state.admin_lock_time).seconds < 30:
            return {"error": "Controlled by another admin. Wait 30 seconds.",
                    "authorized": False}
        else:
            state.admin_lock = False

    state.admin_lock = True
    state.admin_lock_user = user_ip
    state.admin_lock_time = datetime.now()

    state.manual_override = not state.manual_override
    state.pump_status = state.manual_override

    await manager.broadcast({
        "type": "manual",
        "message": f"Manual override "
                   f"{'ENABLED' if state.manual_override else 'DISABLED'} "
                   f"- Pump {'ON' if state.pump_status else 'OFF'}",
    })

    return {
        "manual_override": state.manual_override,
        "pump_status": state.pump_status,
        "authorized": True,
    }
