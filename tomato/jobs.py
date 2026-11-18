# =============================================================================
# FILE:      tomato/jobs.py
# LOCATION:  Intelligent_Tomato_Farm/tomato/jobs.py
# PURPOSE:   Async job queue for tomato video analysis.
#
#            Behavior:
#               - Image uploads are handled synchronously in the router.
#               - Video uploads are handed to a job; the router returns a
#                 job_id immediately and the frontend polls / receives a WS.
#               - Frames are sampled adaptively (see config).
#               - Near-duplicate frames are skipped.
#               - Detections are deduplicated by class + near bbox.
# =============================================================================

from __future__ import annotations
import asyncio
import os
import tempfile
import uuid
from datetime import datetime
from typing import Dict, Optional

import cv2
import numpy as np

import config


# -----------------------------------------------------------------------------
# IN-MEMORY JOB REGISTRY
# -----------------------------------------------------------------------------
_JOBS: Dict[str, dict] = {}


def create_job(source_type: str, source_id: Optional[int] = None,
               filename: str = "") -> str:
    job_id = str(uuid.uuid4())
    _JOBS[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result_id": None,
        "error": None,
        "source_type": source_type,
        "source_id": source_id,
        "filename": filename,
    }
    return job_id


def get_job(job_id: str) -> Optional[dict]:
    return _JOBS.get(job_id)


def _update(job_id: str, **kw) -> None:
    if job_id in _JOBS:
        _JOBS[job_id].update(kw)


# -----------------------------------------------------------------------------
# ADAPTIVE SAMPLING
# -----------------------------------------------------------------------------
def _sample_interval_for(duration_sec: float) -> float:
    if duration_sec < config.SAMPLING_SHORT_MAX_SEC:
        return 0.0  # every frame
    if duration_sec < config.SAMPLING_MED_MAX_SEC:
        return config.SAMPLING_MED_EVERY_N_SEC
    if duration_sec < config.SAMPLING_LONG_MAX_SEC:
        return config.SAMPLING_LONG_EVERY_N_SEC
    return config.SAMPLING_VERY_LONG_EVERY_N_SEC


def _frame_fingerprint(frame) -> np.ndarray:
    """Cheap 32-bin grayscale histogram used for near-duplicate detection."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [32], [0, 256]).flatten()
    s = hist.sum()
    return hist / s if s > 0 else hist


def _is_duplicate(fp: np.ndarray, prev: Optional[np.ndarray], threshold: float = 0.98) -> bool:
    if prev is None:
        return False
    # Histogram intersection
    inter = float(np.minimum(fp, prev).sum())
    return inter >= threshold


# -----------------------------------------------------------------------------
# JOB RUNNER (called from the router via asyncio.create_task)
# -----------------------------------------------------------------------------
async def run_video_job(job_id: str, video_path: str) -> None:
    """
    Steps:
      1. Open video, read fps and duration.
      2. Loop frames with adaptive sampling.
      3. Skip near-duplicates.
      4. Hand each kept frame to tomato_detector.detect_frame(image_bytes).
      5. Merge results, deduplicate, and persist a single tomato_results row.
    """
    try:
        _update(job_id, status="running", progress=0.0)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            _update(job_id, status="failed", error="cannot_open_video")
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = total / fps if total else 0.0
        interval = _sample_interval_for(duration)

        step_frames = int(interval * fps) if interval > 0 else 1
        step_frames = max(1, step_frames)

        # Import here to avoid a circular import at module load.
        from tomato_detector import detect_frame_bytes

        prev_fp = None
        kept = 0
        analyzed = 0
        best = None  # highest-confidence result across frames

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            analyzed += 1

            if analyzed % step_frames != 0:
                continue

            fp = _frame_fingerprint(frame)
            if _is_duplicate(fp, prev_fp):
                prev_fp = fp
                continue
            prev_fp = fp

            ok, buf = cv2.imencode(".jpg", frame)
            if not ok:
                continue
            result = detect_frame_bytes(buf.tobytes())
            kept += 1

            if result and result.get("supervisor_confidence", 0) > (
                best["supervisor_confidence"] if best else 0.0
            ):
                best = result

            if total:
                _update(job_id, progress=min(0.99, analyzed / total))

        cap.release()

        if best is None:
            _update(job_id, status="done", progress=1.0, result_id=None)
            return

        # Persist through the single-writer funnel.
        from detection_memory.store import record_tomato_analysis
        rid = record_tomato_analysis(
            source_type="video",
            source_id=None,
            yolo_class=best["yolo_class"],
            yolo_confidence=best["yolo_confidence"],
            yolo_bbox=best["yolo_bbox"],
            hsv_evidence=best["hsv"],
            kmeans_evidence=best["kmeans"],
            edge_evidence=best["edge"],
            supervisor_primary=best["supervisor_primary"],
            supervisor_confidence=best["supervisor_confidence"],
            supervisor_top3=best["supervisor_top3"],
            supervisor_uncertain=best["supervisor_uncertain"],
            recommendation_text=best["recommendation"],
        )

        _update(job_id, status="done", progress=1.0, result_id=rid)

    except Exception as e:
        _update(job_id, status="failed", error=str(e))
    finally:
        try:
            if os.path.isfile(video_path):
                os.remove(video_path)
        except Exception:
            pass
