# =============================================================================
# FILE:      irrigation/routes/status.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/routes/status.py
# PURPOSE:   GET /api/status and GET /api/recent.
# =============================================================================

from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .. import state
from ..database import db

router = APIRouter()


@router.get("/api/recent")
async def get_recent(limit: int = 30):
    df = db.get_recent_readings(limit=limit)
    if len(df) > 0:
        df["battery_percentage"] = (
            ((df["battery"].astype(float) - 11.0) / 2.5 * 100)
            .round(1).clip(0, 100)
        )
    return JSONResponse(content=df.to_dict(orient="records"))


@router.get("/api/status")
async def get_status():
    recent = db.get_recent_readings(limit=1)
    batt_pct = 0.0
    if len(recent) > 0:
        batt_pct = max(0.0, min(100.0,
                                (float(recent.iloc[0]["battery"]) - 11.0) / 2.5 * 100))
    return {
        "database_entries": db.get_count(),
        "manual_override": state.manual_override,
        "pump_status": state.pump_status,
        "battery_percentage": batt_pct,
        "model_accuracy": state.model_accuracy,
        "samples_trained": state.last_trained_count,
    }
