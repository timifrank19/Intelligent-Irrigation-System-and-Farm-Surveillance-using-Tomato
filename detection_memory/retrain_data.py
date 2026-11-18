# =============================================================================
# FILE:      detection_memory/retrain_data.py
# LOCATION:  Intelligent_Tomato_Farm/detection_memory/retrain_data.py
# PURPOSE:   Reads rows from the supervisor training pool and turns them into
#            (features, labels) arrays ready for train_supervisor.py.
#
#            This is the bridge between the runtime detection loop and the
#            offline supervisor training.
# =============================================================================

from __future__ import annotations
import json
import numpy as np
import pandas as pd
from typing import Tuple, List

from irrigation.database import db


# -----------------------------------------------------------------------------
# FEATURE VECTOR BUILDER
# -----------------------------------------------------------------------------
def _safe(d: dict, key: str, default: float = 0.0) -> float:
    """Read a numeric value from an evidence dict without exploding."""
    try:
        return float(d.get(key, default))
    except Exception:
        return float(default)


def build_feature_vector(row: pd.Series) -> np.ndarray:
    """
    Fixed-length numeric vector describing the four evidence streams.
    Order is stable so the supervisor model can be retrained across runs.

    Layout:
        [ yolo_conf,
          hsv_green, hsv_yellow, hsv_brown, hsv_dark, hsv_abnormal,
          km_cluster_count, km_dominant_cluster_ratio, km_dark_ratio,
          edge_density, edge_lesion_count, edge_mean_edge_len,
          one_hot_yolo_class ... (per class set stored globally in train_supervisor)
        ]
    The one-hot class block is appended by the caller because it depends
    on the class list, which is fixed in train_supervisor.py.
    """
    try:
        hsv = json.loads(row["hsv_json"]) if row["hsv_json"] else {}
    except Exception:
        hsv = {}
    try:
        km = json.loads(row["kmeans_json"]) if row["kmeans_json"] else {}
    except Exception:
        km = {}
    try:
        edge = json.loads(row["edge_json"]) if row["edge_json"] else {}
    except Exception:
        edge = {}

    base = [
        float(row["yolo_confidence"]) if row["yolo_confidence"] is not None else 0.0,
        _safe(hsv, "green_pct"),
        _safe(hsv, "yellow_pct"),
        _safe(hsv, "brown_pct"),
        _safe(hsv, "dark_pct"),
        _safe(hsv, "abnormal_pct"),
        _safe(km, "n_clusters"),
        _safe(km, "dominant_cluster_ratio"),
        _safe(km, "dark_cluster_ratio"),
        _safe(edge, "edge_density"),
        _safe(edge, "lesion_count"),
        _safe(edge, "mean_edge_length"),
    ]
    return np.asarray(base, dtype=np.float32)


# -----------------------------------------------------------------------------
# PUBLIC API
# -----------------------------------------------------------------------------
def export_training_rows(only_confirmed: bool = True) -> Tuple[np.ndarray,
                                                                List[str],
                                                                List[int]]:
    """
    Returns:
        base_features: (N, 12) float array
        yolo_classes : list of yolo_class strings (one per row)
        row_ids      : list of supervisor_training_pool row ids (one per row)

    one-hot encoding of yolo_class is left to the caller, because the class
    list is global and stable across a training session.
    """
    df = db.get_supervisor_pool(only_confirmed=only_confirmed)
    if df is None or len(df) == 0:
        return np.zeros((0, 12), dtype=np.float32), [], []

    feats = np.stack([build_feature_vector(r) for _, r in df.iterrows()])
    yolo_classes = df["yolo_class"].fillna("").tolist()
    ids = df["id"].astype(int).tolist()
    return feats, yolo_classes, ids


def mark_rows_used(ids: List[int]) -> None:
    db.mark_pool_rows_used(ids)
