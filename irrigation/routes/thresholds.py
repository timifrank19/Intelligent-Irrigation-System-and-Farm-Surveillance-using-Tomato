# =============================================================================
# FILE:      irrigation/routes/thresholds.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/routes/thresholds.py
# PURPOSE:   GET /api/thresholds.
# =============================================================================

from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..database import db

router = APIRouter()


@router.get("/api/thresholds")
async def get_thresholds():
    return JSONResponse(content=db.get_thresholds())
