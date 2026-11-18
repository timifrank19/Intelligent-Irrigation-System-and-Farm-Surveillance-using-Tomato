# =============================================================================
# FILE:      api_handler.py
# LOCATION:  Intelligent_Tomato_Farm/api_handler.py
# PURPOSE:   Thin inference dispatcher used by the routers. Keeps HTTP
#            endpoints free of model-loading logic.
#
#            - run_human_animal(frame_bytes, mode) -> detection dict
#            - run_tomato(frame_bytes)               -> analysis dict
#            - run_tomato_video_frames(...)          -> used by job runner
# =============================================================================

from __future__ import annotations
from typing import Optional


def run_human_animal(frame_bytes: bytes, mode: str = "auto") -> dict:
    from human_animal_detector import detect_all
    return detect_all(frame_bytes, requested_mode=mode)


def run_tomato(frame_bytes: bytes) -> Optional[dict]:
    from tomato_detector import detect_frame_bytes
    return detect_frame_bytes(frame_bytes)


def health() -> dict:
    import os
    import config

    return {
        "status": "ok",
        "models": {
            "human_day": os.path.isfile(config.HUMAN_DAY_MODEL),
            "human_night": os.path.isfile(config.HUMAN_NIGHT_MODEL),
            "animal_day": os.path.isfile(config.ANIMAL_DAY_MODEL),
            "animal_night": os.path.isfile(config.ANIMAL_NIGHT_MODEL),
            "tomato_leaf": os.path.isfile(config.TOMATO_LEAF_MODEL),
            "tomato_fruit": os.path.isfile(config.TOMATO_FRUIT_MODEL),
            "supervisor": os.path.isfile(config.SUPERVISOR_MODEL),
        },
    }
