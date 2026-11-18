# =============================================================================
# FILE:      detection_memory/store.py
# LOCATION:  Intelligent_Tomato_Farm/detection_memory/store.py
# PURPOSE:   Single funnel for writing detection evidence into the database.
#            Nothing else in the project writes directly to these tables.
#
#            Responsibilities:
#              - store a surveillance detection event
#              - store a tomato analysis result (DB + JSON file)
#              - store a row in the supervisor training pool
# =============================================================================

from __future__ import annotations
import json
import os
from datetime import datetime
from typing import Optional

import config
from irrigation.database import db


# -----------------------------------------------------------------------------
# SURVEILLANCE EVENTS
# -----------------------------------------------------------------------------
def record_surveillance_event(
    recording_id: Optional[int],
    frame_id: int,
    class_name: str,
    confidence: float,
    bbox,
    mode: str,
    source: str = "live",
) -> None:
    """
    Insert one detection event row.
    bbox is any JSON-serializable structure (list/tuple/dict) and is stored
    as a JSON string so the schema stays stable.
    """
    db.insert_surveillance_event(
        recording_id=recording_id,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        frame_id=frame_id,
        class_name=class_name,
        confidence=float(confidence),
        bbox_json=json.dumps(list(bbox)),
        mode=mode,
        source=source,
    )


# -----------------------------------------------------------------------------
# TOMATO ANALYSIS RESULT (DB + JSON)
# -----------------------------------------------------------------------------
def record_tomato_analysis(
    source_type: str,                # "image" | "video" | "surveillance"
    source_id: Optional[int],
    yolo_class: str,
    yolo_confidence: float,
    yolo_bbox,
    hsv_evidence: dict,
    kmeans_evidence: dict,
    edge_evidence: dict,
    supervisor_primary: str,
    supervisor_confidence: float,
    supervisor_top3: list,
    supervisor_uncertain: bool,
    recommendation_text: str,
) -> int:
    """
    Persist one tomato analysis in two places:
        1. SQLite row in `tomato_results`
        2. JSON file in results/
    Returns the database row id.
    """

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- write the JSON file first so we know its path ----------------------
    json_name = f"tomato_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
    json_path = os.path.join(config.RESULTS_DIR, json_name)
    record = {
        "timestamp": ts,
        "source_type": source_type,
        "source_id": source_id,
        "yolo": {
            "class": yolo_class,
            "confidence": float(yolo_confidence),
            "bbox": list(yolo_bbox) if yolo_bbox is not None else None,
        },
        "hsv": hsv_evidence,
        "kmeans": kmeans_evidence,
        "edge": edge_evidence,
        "supervisor": {
            "primary": supervisor_primary,
            "confidence": float(supervisor_confidence),
            "top3": supervisor_top3,
            "uncertain": bool(supervisor_uncertain),
        },
        "recommendation": recommendation_text,
    }
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
    except Exception as e:
        print(f"[detection_memory] Failed to write JSON result: {e}")
        json_path = None

    # --- then the DB row -----------------------------------------------------
    rid = db.insert_tomato_result(
        timestamp=ts,
        source_type=source_type,
        source_id=source_id,
        yolo_class=yolo_class,
        yolo_confidence=float(yolo_confidence),
        yolo_bbox_json=json.dumps(list(yolo_bbox)) if yolo_bbox is not None else None,
        hsv_json=json.dumps(hsv_evidence),
        kmeans_json=json.dumps(kmeans_evidence),
        edge_json=json.dumps(edge_evidence),
        supervisor_primary=supervisor_primary,
        supervisor_confidence=float(supervisor_confidence),
        supervisor_top3_json=json.dumps(supervisor_top3),
        supervisor_uncertain=int(bool(supervisor_uncertain)),
        recommendation_text=recommendation_text,
        user_confirmed=0,
        user_true_class=None,
        result_json_path=json_path,
    )

    # --- and a row in the supervisor training pool --------------------------
    # Pseudo-label only if the supervisor is confident. Otherwise leave it
    # empty for admin confirmation.
    ground_truth = None
    label_source = None
    if supervisor_confidence >= config.SUPERVISOR_PSEUDO_LABEL_CONF and not supervisor_uncertain:
        ground_truth = supervisor_primary
        label_source = "pseudo"

    record_supervisor_pool_row(
        tomato_result_id=rid,
        yolo_class=yolo_class,
        yolo_confidence=float(yolo_confidence),
        hsv_evidence=hsv_evidence,
        kmeans_evidence=kmeans_evidence,
        edge_evidence=edge_evidence,
        supervisor_primary=supervisor_primary,
        supervisor_confidence=float(supervisor_confidence),
        ground_truth=ground_truth,
        label_source=label_source,
    )

    return rid


# -----------------------------------------------------------------------------
# SUPERVISOR TRAINING POOL
# -----------------------------------------------------------------------------
def record_supervisor_pool_row(
    tomato_result_id: Optional[int],
    yolo_class: str,
    yolo_confidence: float,
    hsv_evidence: dict,
    kmeans_evidence: dict,
    edge_evidence: dict,
    supervisor_primary: str,
    supervisor_confidence: float,
    ground_truth: Optional[str] = None,
    label_source: Optional[str] = None,
) -> int:
    return db.insert_supervisor_pool_row(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        tomato_result_id=tomato_result_id,
        yolo_class=yolo_class,
        yolo_confidence=float(yolo_confidence),
        hsv_json=json.dumps(hsv_evidence),
        kmeans_json=json.dumps(kmeans_evidence),
        edge_json=json.dumps(edge_evidence),
        supervisor_primary=supervisor_primary,
        supervisor_confidence=float(supervisor_confidence),
        ground_truth=ground_truth,
        label_source=label_source,
        used_in_training=0,
    )
