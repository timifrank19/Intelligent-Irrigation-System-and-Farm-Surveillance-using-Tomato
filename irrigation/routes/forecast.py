# =============================================================================
# FILE:      irrigation/routes/forecast.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/routes/forecast.py
# PURPOSE:   GET /api/forecast.
# =============================================================================

from __future__ import annotations
from fastapi import APIRouter

from ..forecast import build_forecast

router = APIRouter()


@router.get("/api/forecast")
async def get_forecast():
    return build_forecast(limit=50)
