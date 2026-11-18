# =============================================================================
# FILE:      surveillance/recordings.py
# LOCATION:  Intelligent_Tomato_Farm/surveillance/recordings.py
# PURPOSE:   Handles the full lifecycle of surveillance recording chunks:
#
#               1. Receive a 5-minute chunk from the frontend.
#               2. Check event_count for that chunk.
#               3. If event_count == 0  -> discard (never stored).
#               4. If event_count  > 0  -> store BLOB, link events.
#               5. Sweeper deletes recordings 7 days after analysis.
#               6. Sweeper warns 1 hour before deletion.
#               7. Bundle builder produces a ZIP containing video + JSON.
# =============================================================================

from __future__ import annotations
import asyncio
import io
import json
import os
import zipfile
from datetime import datetime, timedelta
from typing import Optional

from irrigation.database import db
import config
from .events import (
    recording_warning_payload,
    recording_deleted_payload,
    broadcast,
)


# -----------------------------------------------------------------------------
# CHUNK INGESTION
# -----------------------------------------------------------------------------
def ingest_chunk(
    filename: str,
    data: bytes,
    duration_sec: float,
    mode: str,
    event_count: int,
) -> dict:
    """
    Called by the router when a 5-minute chunk arrives.
    Applies the keep / discard rule:
        event_count == 0 -> discard
        event_count  > 0 -> store
    """
    if event_count <= 0:
        return {"kept": False, "reason": "no_detections"}

    rec_id = db.insert_recording(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        filename=filename,
        size=len(data),
        duration_sec=float(duration_sec),
        mode=mode,
        event_count=int(event_count),
        data=data,
    )
    return {"kept": True, "recording_id": rec_id}


# -----------------------------------------------------------------------------
# ANALYSIS HOOK
# -----------------------------------------------------------------------------
def mark_analyzed(recording_id: int) -> None:
    """
    Called by tomato analysis when a recording has been processed.
    Schedules deletion 7 days from now.
    """
    delete_at = (datetime.now() +
                 timedelta(days=config.ANALYZED_RETENTION_DAYS)
                 ).strftime("%Y-%m-%d %H:%M:%S")
    db.mark_recording_analyzed(recording_id, delete_at)


# -----------------------------------------------------------------------------
# BUNDLE BUILDER (on demand, not stored on disk)
# -----------------------------------------------------------------------------
def build_bundle(recording_id: int) -> Optional[bytes]:
    """
    Build a ZIP containing:
        video.webm  (or original filename)
        events.json (all surveillance_events for this recording)
        tomato.json (the tomato_result row if it exists, else null)
        manifest.json
    Returns the ZIP bytes, or None if the recording does not exist.
    """
    rec = db.get_recording(recording_id)
    if rec is None:
        return None

    # events
    conn = db.db_path and None  # quiet linter
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM surveillance_events WHERE recording_id = ? ORDER BY id ASC",
        (recording_id,),
    )
    events = [dict(r) for r in cur.fetchall()]

    cur.execute(
        "SELECT * FROM tomato_results WHERE source_type = 'surveillance' "
        "AND source_id = ? ORDER BY id DESC LIMIT 1",
        (recording_id,),
    )
    tomato_row = cur.fetchone()
    tomato = dict(tomato_row) if tomato_row else None
    conn.close()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        # video
        try:
            z.writestr(rec["filename"], rec["data"])
        except Exception as e:
            print(f"[recordings] Failed to embed video: {e}")

        # events
        z.writestr("events.json", json.dumps(events, indent=2, default=str))

        # tomato
        z.writestr("tomato.json", json.dumps(tomato, indent=2, default=str))

        # manifest
        manifest = {
            "recording_id": recording_id,
            "timestamp": rec["timestamp"],
            "filename": rec["filename"],
            "size": rec["size"],
            "duration_sec": rec["duration_sec"],
            "mode": rec["mode"],
            "event_count": rec["event_count"],
            "analyzed_at": rec["analyzed_at"],
            "deletion_at": rec["deletion_at"],
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        z.writestr("manifest.json", json.dumps(manifest, indent=2, default=str))

    return buf.getvalue()


# -----------------------------------------------------------------------------
# BACKGROUND SWEEPER
# -----------------------------------------------------------------------------
async def sweeper_loop():
    """
    Runs every SWEEPER_INTERVAL_SEC.
      - Warn 1 hour before deletion.
      - Delete after deletion_at passes.
    """
    while True:
        try:
            _run_sweep_once()
        except Exception as e:
            print(f"[recordings] Sweeper error: {e}")
        await asyncio.sleep(config.SWEEPER_INTERVAL_SEC)


def _run_sweep_once() -> None:
    rows = db.list_recordings(only_analyzed=True)
    now = datetime.now()

    for r in rows:
        rec_id = r["id"]
        deletion_at = r.get("deletion_at")
        notified = r.get("notified_at")
        if not deletion_at:
            continue
        try:
            del_dt = datetime.strptime(deletion_at, "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue

        # 1 hour warning
        if (not notified) and (del_dt - now) <= timedelta(seconds=config.DELETION_WARNING_SECONDS):
            # fire-and-forget broadcast
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(broadcast(recording_warning_payload(rec_id, r["filename"])))
            except Exception:
                pass
            db.mark_recording_notified(rec_id)

        # delete
        if now >= del_dt:
            try:
                db.delete_recording(rec_id)
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(broadcast(recording_deleted_payload(rec_id)))
                except Exception:
                    pass
                print(f"[recordings] Deleted recording {rec_id} (aged past retention).")
            except Exception as e:
                print(f"[recordings] Failed to delete {rec_id}: {e}")
