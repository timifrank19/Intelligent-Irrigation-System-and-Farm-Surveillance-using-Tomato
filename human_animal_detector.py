# =============================================================================
# FILE:      human_animal_detector.py
# LOCATION:  Intelligent_Tomato_Farm/human_animal_detector.py
# PURPOSE:   Real-time human + animal detection with day/night model selection.
#
#            Models (loaded lazily, cached):
#               human_day.pt
#               human_night.pt
#               animal_day.pt
#               animal_night.pt
#
#            Mode selection:
#               "day"   -> use *_day.pt
#               "night" -> use *_night.pt
#               "auto"  -> inspect the frame chroma to decide
# =============================================================================

from __future__ import annotations
import io
import os
import numpy as np
import cv2
from PIL import Image

import config


# -----------------------------------------------------------------------------
# MODEL CACHE
# -----------------------------------------------------------------------------
_MODELS = {}


def _load(path: str):
    if path in _MODELS:
        return _MODELS[path]
    if not os.path.isfile(path):
        _MODELS[path] = None
        return None
    try:
        from ultralytics import YOLO
        _MODELS[path] = YOLO(path)
        print(f"[human_animal_detector] Loaded {path}")
    except Exception as e:
        print(f"[human_animal_detector] Failed to load {path}: {e}")
        _MODELS[path] = None
    return _MODELS[path]


# -----------------------------------------------------------------------------
# MODE DETECTION
# -----------------------------------------------------------------------------
def _is_likely_ir(bgr: np.ndarray) -> bool:
    """
    IR/gray frames have near-zero chroma. Use std of (S channel) as a proxy.
    Threshold comes from config so it can be tuned.
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    return float(np.std(hsv[:, :, 1])) < config.CHROMA_THRESHOLD


# -----------------------------------------------------------------------------
# DETECTION
# -----------------------------------------------------------------------------
def _infer(model, bgr: np.ndarray, conf: float) -> list:
    if model is None:
        return []
    results = model.predict(bgr, conf=conf, verbose=False)
    out = []
    for r in results:
        if r.boxes is None:
            continue
        for b in r.boxes:
            cls_id = int(b.cls[0].item())
            name = model.names[cls_id]
            conf_v = float(b.conf[0].item())
            xyxy = b.xyxy[0].tolist()
            out.append({
                "class_name": name,
                "confidence": round(conf_v, 4),
                "bbox": [float(v) for v in xyxy],
            })
    return out


# -----------------------------------------------------------------------------
# PUBLIC API
# -----------------------------------------------------------------------------
def detect_all(image_bytes: bytes, requested_mode: str = "auto") -> dict:
    """
    Returns:
        {
          mode: "day"|"night",
          humans: [ {class_name, confidence, bbox}, ... ],
          animals: [ {class_name, confidence, bbox}, ... ]
        }
    """
    bgr = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))[:, :, ::-1]

    if requested_mode == "day":
        mode = "day"
    elif requested_mode == "night":
        mode = "night"
    else:
        mode = "night" if _is_likely_ir(bgr) else "day"

    human_model_path = config.HUMAN_DAY_MODEL if mode == "day" else config.HUMAN_NIGHT_MODEL
    animal_model_path = config.ANIMAL_DAY_MODEL if mode == "day" else config.ANIMAL_NIGHT_MODEL

    human_model = _load(human_model_path)
    animal_model = _load(animal_model_path)

    humans = _infer(human_model, bgr, conf=config.SURVEILLANCE_KEEP_THRESHOLD)
    animals = _infer(animal_model, bgr, conf=config.SURVEILLANCE_KEEP_THRESHOLD)

    # Filter humans out of animals if the animal model happens to include person.
    animals = [a for a in animals if a["class_name"].lower() != "person"]

    return {"mode": mode, "humans": humans, "animals": animals}
