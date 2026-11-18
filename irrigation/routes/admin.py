# =============================================================================
# FILE:      irrigation/routes/admin.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/routes/admin.py
# PURPOSE:   Admin-only irrigation endpoints.
# FIX 13:    All three endpoints sit behind require_admin; the frontend uses
#            /api/admin/check to validate the stored key.
# CORRECTION: /api/retrain now returns HTTP 409 when retraining cannot run
#            (too few readings) instead of a 200 that hides the failure. The
#            body still carries {"message": ...}, which controls.js displays.
#            Training errors are caught and reported as HTTP 500.
# =============================================================================

from __future__ import annotations
import io
import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from .. import state
from ..database import db
from ..models import train_ai_model
from surveillance.auth import require_admin

router = APIRouter()


@router.get("/api/admin/check", dependencies=[Depends(require_admin)])
async def admin_check():
    """Frontend uses this to validate the stored key."""
    return {"authorized": True}


@router.post("/api/retrain", dependencies=[Depends(require_admin)])
async def retrain_models():
    try:
        ok = await asyncio.to_thread(train_ai_model)
    except Exception as e:
        return JSONResponse(status_code=500,
                            content={"message": f"Retraining error: {e}"})
    if ok:
        return {"message": f"Model retrained! Accuracy: {state.model_accuracy:.2%}"}
    return JSONResponse(
        status_code=409,
        content={"message": "Retraining failed — insufficient data"},
    )


@router.get("/api/export", dependencies=[Depends(require_admin)])
async def export_data():
    df = db.get_all_readings()
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=irrigation_data.csv"},
    )
