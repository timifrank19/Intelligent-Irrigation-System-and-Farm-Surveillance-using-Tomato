# =============================================================================
# FILE:      tomato_detector.py
# LOCATION:  Intelligent_Tomato_Farm/tomato_detector.py
# PURPOSE:   Tomato disease pipeline:
#
#               1. Decode frame
#               2. Reject IR/grayscale input (RGB required)
#               3. Run YOLOv8 leaf or fruit model
#               4. Take the highest-confidence ROI
#               5. Run HSV, K-means, Edge analyzers INDEPENDENTLY on the ROI
#               6. Pass all four evidence streams to the supervisor
#               7. Pass the supervisor's decision to recommendation
#               8. Return a single dict ready for storage and UI
#
#            Leaf vs fruit model choice:
#               - If both are loaded, we pick whichever model reports
#                 the higher-confidence detection on this frame.
# =============================================================================

from __future__ import annotations
import io
import os
import numpy as np
import cv2
from PIL import Image
from typing import Optional

import config
from hsv_analyzer import analyze_roi as hsv_analyze
from kmeans_analyzer import analyze_roi as kmeans_analyze
from edge_analyzer import analyze_roi as edge_analyze
import supervisor as sv
from recommendation import recommend


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
        print(f"[tomato_detector] Loaded {path}")
    except Exception as e:
        print(f"[tomato_detector] Failed to load {path}: {e}")
        _MODELS[path] = None
    return _MODELS[path]


# -----------------------------------------------------------------------------
# COLOR CHECK
# -----------------------------------------------------------------------------
def _is_likely_ir(bgr: np.ndarray) -> bool:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    return float(np.std(hsv[:, :, 1])) < config.CHROMA_THRESHOLD


# -----------------------------------------------------------------------------
# DETECTION
# -----------------------------------------------------------------------------
def _top_detection(model, bgr: np.ndarray, conf: float = config.YOLO_CONF_DEFAULT):
    if model is None:
        return None
    res = model.predict(bgr, conf=conf, verbose=False)
    if not res:
        return None
    r = res[0]
    if r.boxes is None or len(r.boxes) == 0:
        return None

    # pick highest confidence box
    best_idx = int(np.argmax([float(b.conf[0].item()) for b in r.boxes]))
    b = r.boxes[best_idx]
    cls_id = int(b.cls[0].item())
    name = model.names[cls_id]
    conf_v = float(b.conf[0].item())
    x1, y1, x2, y2 = [float(v) for v in b.xyxy[0].tolist()]
    return {
        "class_name": name,
        "confidence": round(conf_v, 4),
        "bbox": [x1, y1, x2, y2],
    }


# -----------------------------------------------------------------------------
# PUBLIC API
# -----------------------------------------------------------------------------
def detect_frame_bytes(image_bytes: bytes,
                       model_hint: Optional[str] = None) -> Optional[dict]:
    """
    model_hint: "leaf" | "fruit" | None
        If None, both models are tried and the higher-confidence one is used.
    """
    pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    bgr = np.array(pil)[:, :, ::-1]

    if _is_likely_ir(bgr):
        return {
            "error": "ir_input_rejected",
            "message": "Tomato disease detection requires RGB. IR/grayscale "
                       "input cannot be analyzed for tomato disease.",
        }

    leaf_model = _load(config.TOMATO_LEAF_MODEL)
    fruit_model = _load(config.TOMATO_FRUIT_MODEL)

    candidates = []
    if model_hint == "leaf" and leaf_model is not None:
        det = _top_detection(leaf_model, bgr)
        if det:
            candidates.append((det, "leaf"))
    elif model_hint == "fruit" and fruit_model is not None:
        det = _top_detection(fruit_model, bgr)
        if det:
            candidates.append((det, "fruit"))
    else:
        if leaf_model is not None:
            det = _top_detection(leaf_model, bgr)
            if det:
                candidates.append((det, "leaf"))
        if fruit_model is not None:
            det = _top_detection(fruit_model, bgr)
            if det:
                candidates.append((det, "fruit"))

    if not candidates:
        return None

    # pick highest-confidence
    det, kind = max(candidates, key=lambda x: x[0]["confidence"])

    # crop ROI
    x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
    h, w = bgr.shape[:2]
    x1 = max(0, x1); y1 = max(0, y1)
    x2 = min(w, x2); y2 = min(h, y2)
    roi = bgr[y1:y2, x1:x2]
    if roi.size == 0:
        return None

    # three independent analyses
    hsv_ev = hsv_analyze(roi)
    km_ev = kmeans_analyze(roi)
    ed_ev = edge_analyze(roi)

    # supervisor
    decision = sv.decide(
        yolo_class=det["class_name"],
        yolo_confidence=det["confidence"],
        hsv=hsv_ev,
        kmeans=km_ev,
        edge=ed_ev,
    )

    rec = recommend(decision["primary"], uncertain=decision["uncertain"])

    return {
        "kind": kind,                       # "leaf" or "fruit"
        "yolo_class": det["class_name"],
        "yolo_confidence": det["confidence"],
        "yolo_bbox": det["bbox"],
        "hsv": hsv_ev,
        "kmeans": km_ev,
        "edge": ed_ev,
        "supervisor_primary": decision["primary"],
        "supervisor_confidence": decision["confidence"],
        "supervisor_top3": decision["top3"],
        "supervisor_uncertain": decision["uncertain"],
        "supervisor_fallback": decision.get("fallback", False),
        "recommendation": rec,
    }
