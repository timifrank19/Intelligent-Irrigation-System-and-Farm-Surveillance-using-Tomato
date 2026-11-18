# =============================================================================
# FILE:      tomato/router.py
# LOCATION:  Intelligent_Tomato_Farm/tomato/router.py
# PURPOSE:   Tomato endpoints:
#               POST /api/tomato/image             (instant)
#               POST /api/tomato/video             (async job)
#               GET  /api/tomato/job/{job_id}      (poll job status)
#               GET  /api/tomato/results           (recent results list)
#               GET  /api/tomato/results/{id}      (one result)
#               POST /api/tomato/confirm/{id}      (Yes/No admin feedback)
#               POST /api/tomato/analyze_recording/{rec_id}  (from surveillance)
# =============================================================================

from __future__ import annotations
import asyncio
import os
import tempfile
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
import cv2

from surveillance.auth import require_admin
from . import jobs
from . import results as results_api
from irrigation.database import db
import config

router = APIRouter(prefix="/api/tomato", tags=["tomato"])


# -----------------------------------------------------------------------------
# IMAGE — instant path
# -----------------------------------------------------------------------------
@router.post("/image", dependencies=[Depends(require_admin)])
async def analyze_image(file: UploadFile = File(...)):
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(400, "empty_image")

    try:
        from tomato_detector import detect_frame_bytes
    except Exception as e:
        raise HTTPException(500, f"tomato_detector unavailable: {e}")

    result = detect_frame_bytes(image_bytes)
    if result is None:
        return {"status": "ok", "found": False}

    from detection_memory.store import record_tomato_analysis
    rid = record_tomato_analysis(
        source_type="image",
        source_id=None,
        yolo_class=result["yolo_class"],
        yolo_confidence=result["yolo_confidence"],
        yolo_bbox=result["yolo_bbox"],
        hsv_evidence=result["hsv"],
        kmeans_evidence=result["kmeans"],
        edge_evidence=result["edge"],
        supervisor_primary=result["supervisor_primary"],
        supervisor_confidence=result["supervisor_confidence"],
        supervisor_top3=result["supervisor_top3"],
        supervisor_uncertain=result["supervisor_uncertain"],
        recommendation_text=result["recommendation"],
    )

    return {"status": "ok", "found": True, "result_id": rid, "data": result}


# -----------------------------------------------------------------------------
# VIDEO — async path
# -----------------------------------------------------------------------------
@router.post("/video", dependencies=[Depends(require_admin)])
async def analyze_video(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty_video")

    # Persist to a temp file that the job will read then remove.
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp.write(data)
    tmp.close()

    job_id = jobs.create_job("video", filename=file.filename or "upload.mp4")
    asyncio.create_task(jobs.run_video_job(job_id, tmp.name))
    return {"status": "queued", "job_id": job_id}


@router.get("/job/{job_id}", dependencies=[Depends(require_admin)])
async def job_status(job_id: str):
    j = jobs.get_job(job_id)
    if not j:
        raise HTTPException(404, "job_not_found")
    return j


# -----------------------------------------------------------------------------
# RESULTS
# -----------------------------------------------------------------------------
@router.get("/results", dependencies=[Depends(require_admin)])
async def list_results(limit: int = 50):
    return {"results": results_api.list_recent(limit=limit)}


@router.get("/results/{result_id}", dependencies=[Depends(require_admin)])
async def get_result(result_id: int):
    row = results_api.get_result(result_id)
    if not row:
        raise HTTPException(404, "result_not_found")
    row["json"] = results_api.load_json_for_result(result_id)
    return row


@router.post("/confirm/{result_id}", dependencies=[Depends(require_admin)])
async def confirm_result(result_id: int,
                        is_correct: bool = Form(...),
                        true_class: Optional[str] = Form(None)):
    out = results_api.confirm_result(result_id, is_correct, true_class)
    if not out.get("updated"):
        raise HTTPException(400, out.get("reason", "failed"))
    return out


# -----------------------------------------------------------------------------
# ANALYZE A STORED SURVEILLANCE RECORDING
# -----------------------------------------------------------------------------
@router.post("/analyze_recording/{rec_id}", dependencies=[Depends(require_admin)])
async def analyze_stored_recording(rec_id: int):
    rec = db.get_recording(rec_id)
    if not rec:
        raise HTTPException(404, "recording_not_found")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    tmp.write(rec["data"])
    tmp.close()

    job_id = jobs.create_job("surveillance", source_id=rec_id,
                             filename=rec["filename"])
    asyncio.create_task(jobs.run_video_job(job_id, tmp.name))

    # When the job finishes, mark the recording as analyzed so the
    # retention clock starts.
    async def _wait_and_mark():
        while True:
            j = jobs.get_job(job_id)
            if j and j["status"] in ("done", "failed"):
                break
            await asyncio.sleep(2)
        if j and j["status"] == "done":
            from surveillance.recordings import mark_analyzed
            mark_analyzed(rec_id)

    asyncio.create_task(_wait_and_mark())
    return {"status": "queued", "job_id": job_id, "recording_id": rec_id}

tomato_router = router
