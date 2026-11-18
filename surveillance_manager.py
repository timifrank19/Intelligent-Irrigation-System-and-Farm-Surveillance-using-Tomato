# =============================================================================
# FILE:      surveillance_manager.py
# LOCATION:  Intelligent_Tomato_Farm/surveillance_manager.py
# PURPOSE:   Orchestrates real-time surveillance processing:
#               - receives a frame (JPEG bytes)
#               - runs detection
#               - stores events in the database
#               - broadcasts WebSocket events
#            The HTTP router calls this module; the actual YOLO logic lives
#            in human_animal_detector.
# =============================================================================

from __future__ import annotations
from datetime import datetime
from typing import Optional

from human_animal_detector import detect_all
from detection_memory.store import record_surveillance_event
from surveillance.events import (
    human_event_payload,
    animal_event_payload,
    broadcast,
)


async def process_frame(
    image_bytes: bytes,
    mode: str = "auto",
    recording_id: Optional[int] = None,
    frame_id: int = 0,
) -> dict:
    """
    Returns the same shape as human_animal_detector.detect_all but also
    persists events and broadcasts them.
    """
    result = detect_all(image_bytes, requested_mode=mode)

    # Persist + broadcast humans
    for h in result["humans"]:
        record_surveillance_event(
            recording_id=recording_id,
            frame_id=frame_id,
            class_name=h["class_name"],
            confidence=h["confidence"],
            bbox=h["bbox"],
            mode=result["mode"],
            source="live",
        )

    for a in result["animals"]:
        record_surveillance_event(
            recording_id=recording_id,
            frame_id=frame_id,
            class_name=a["class_name"],
            confidence=a["confidence"],
            bbox=a["bbox"],
            mode=result["mode"],
            source="live",
        )

    if result["humans"]:
        await broadcast(human_event_payload(result["humans"], result["mode"]))
    if result["animals"]:
        await broadcast(animal_event_payload(result["animals"], result["mode"]))

    return result
