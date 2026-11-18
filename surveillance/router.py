# =============================================================================
# FILE:      surveillance/router.py
# LOCATION:  Intelligent_Tomato_Farm/surveillance/router.py
# PURPOSE:   Surveillance endpoints:
#               POST /api/surveillance/frame          (one frame inference)
#               POST /api/surveillance/recordings     (5-min chunk upload)
#               GET  /api/surveillance/recordings     (list)
#               GET  /api/surveillance/recordings/{id}/bundle (ZIP)
#               GET  /api/surveillance/events         (recent events)
#               GET  /api/surveillance/mode           (current mode)
#               POST /api/surveillance/mode           (set day/night/auto)
# =============================================================================

from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse

from .auth import require_admin
from . import recordings as rec_store
from .events import human_event_payload, animal_event_payload, broadcast
from irrigation.database import db

router = APIRouter(prefix="/api/surveillance", tags=["surveillance"])


# -----------------------------------------------------------------------------
# FRAME INFERENCE (called repeatedly by the frontend)
# -----------------------------------------------------------------------------
@router.post("/frame", dependencies=[Depends(require_admin)])
async def process_frame(
    file: UploadFile = File(...),
    mode: str = Form("auto"),
):
    """
    Runs human + animal detection on one frame.
    The heavy lifting lives in human_animal_detector to keep this router thin.
    """
    try:
        from human_animal_detector import detect_all
    except Exception as e:
        raise HTTPException(500, f"detector unavailable: {e}")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(400, "empty_frame")

    result = detect_all(image_bytes, requested_mode=mode)

    # Broadcast human/animal events if any
    if result["humans"]:
        await broadcast(human_event_payload(result["humans"], result["mode"]))
    if result["animals"]:
        await broadcast(animal_event_payload(result["animals"], result["mode"]))

    return {
        "status": "ok",
        "mode": result["mode"],
        "humans": result["humans"],
        "animals": result["animals"],
    }


# -----------------------------------------------------------------------------
# RECORDING CHUNKS
# -----------------------------------------------------------------------------
@router.post("/recordings", dependencies=[Depends(require_admin)])
async def upload_recording(
    file: UploadFile = File(...),
    duration_sec: float = Form(300.0),
    mode: str = Form("auto"),
    event_count: int = Form(0),
):
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty_recording")

    result = rec_store.ingest_chunk(
        filename=file.filename or f"chunk_{datetime.now():%Y%m%d_%H%M%S}.webm",
        data=data,
        duration_sec=duration_sec,
        mode=mode,
        event_count=event_count,
    )
    return result


@router.get("/recordings", dependencies=[Depends(require_admin)])
async def list_recordings(analyzed_only: bool = False):
    return {"recordings": db.list_recordings(only_analyzed=analyzed_only)}


@router.get("/recordings/{rec_id}/bundle", dependencies=[Depends(require_admin)])
async def download_bundle(rec_id: int):
    blob = rec_store.build_bundle(rec_id)
    if blob is None:
        raise HTTPException(404, "recording_not_found")
    return StreamingResponse(
        iter([blob]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=recording_{rec_id}.zip"},
    )


# -----------------------------------------------------------------------------
# EVENTS
# -----------------------------------------------------------------------------
@router.get("/events", dependencies=[Depends(require_admin)])
async def recent_events(limit: int = 100):
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM surveillance_events ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"events": rows}


# -----------------------------------------------------------------------------
# MODE (day / night / auto)
# -----------------------------------------------------------------------------
_MODE_STATE = {"mode": "auto"}


@router.get("/mode")
async def get_mode():
    return _MODE_STATE


@router.post("/mode", dependencies=[Depends(require_admin)])
async def set_mode(mode: str = Form("auto")):
    if mode not in ("auto", "day", "night"):
        raise HTTPException(400, "invalid_mode")
    _MODE_STATE["mode"] = mode
    return _MODE_STATE

surveillance_router = router
