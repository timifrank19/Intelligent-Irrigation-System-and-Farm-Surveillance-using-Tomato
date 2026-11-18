# =============================================================================
# FILE:      surveillance/events.py
# LOCATION:  Intelligent_Tomato_Farm/surveillance/events.py
# PURPOSE:   Helper functions to build and broadcast surveillance events
#            over the single shared WebSocket channel.
# =============================================================================

from __future__ import annotations
from datetime import datetime
from typing import List, Dict

from irrigation.websocket import manager


def human_event_payload(detections: List[Dict], mode: str) -> dict:
    return {
        "type": "human_detected",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": mode,
        "detections": detections,
    }


def animal_event_payload(detections: List[Dict], mode: str) -> dict:
    return {
        "type": "animal_detected",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": mode,
        "detections": detections,
    }


def recording_warning_payload(recording_id: int, filename: str) -> dict:
    return {
        "type": "recording_warning",
        "recording_id": recording_id,
        "filename": filename,
        "message": "Recording will be deleted in 1 hour. Download the bundle now.",
    }


def recording_deleted_payload(recording_id: int) -> dict:
    return {
        "type": "recording_deleted",
        "recording_id": recording_id,
    }


async def broadcast(payload: dict) -> None:
    await manager.broadcast(payload)
