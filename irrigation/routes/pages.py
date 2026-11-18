# =============================================================================
# FILE:      irrigation/routes/pages.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/routes/pages.py
# PURPOSE:   GET / serves the single-page frontend.
# =============================================================================

from __future__ import annotations
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from .. import config as cfg

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root():
    project_root = os.path.dirname(os.path.dirname(cfg.__file__))
    index_path = os.path.join(project_root, "frontend", "index.html")
    if not os.path.isfile(index_path):
        raise HTTPException(status_code=500,
                            detail=f"frontend/index.html not found at {index_path}")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())
