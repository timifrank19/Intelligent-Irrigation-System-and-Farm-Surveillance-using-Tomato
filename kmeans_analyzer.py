# =============================================================================
# FILE:      kmeans_analyzer.py
# LOCATION:  Intelligent_Tomato_Farm/kmeans_analyzer.py
# PURPOSE:   Independent K-means colour-cluster analysis of the same ROI.
#            Runs on its own; does NOT depend on hsv_analyzer output.
# =============================================================================

from __future__ import annotations
import cv2
import numpy as np


K = 4   # small number of colour clusters keeps runtime predictable


def analyze_roi(roi_bgr: np.ndarray, k: int = K) -> dict:
    if roi_bgr is None or roi_bgr.size == 0:
        return _empty_result()

    # Downsample for speed (keeps colour distribution).
    h, w = roi_bgr.shape[:2]
    scale = max(1, int(np.sqrt(h * w) / 120))
    small = cv2.resize(roi_bgr, (max(8, w // scale), max(8, h // scale)))

    data = small.reshape(-1, 3).astype(np.float32)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 15, 1.0)
    _, labels, centers = cv2.kmeans(
        data, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS
    )

    labels = labels.flatten()
    counts = np.bincount(labels, minlength=k).astype(np.float32)
    total = counts.sum() if counts.sum() > 0 else 1.0
    ratios = counts / total

    dominant_idx = int(np.argmax(ratios))

    # Classify each cluster center as dark/green/red/yellow/brown by HSV.
    centers_u8 = centers.astype(np.uint8).reshape(-1, 1, 3)
    centers_hsv = cv2.cvtColor(centers_u8, cv2.COLOR_BGR2HSV).reshape(-1, 3)

    dark_ratio = 0.0
    green_ratio = 0.0
    red_ratio = 0.0
    for i in range(k):
        hh, ss, vv = centers_hsv[i]
        if vv < 60:
            dark_ratio += ratios[i]
        elif 35 <= hh <= 85:
            green_ratio += ratios[i]
        elif hh <= 10 or hh >= 170:
            red_ratio += ratios[i]

    return {
        "n_clusters": int(k),
        "dominant_cluster_index": dominant_idx,
        "dominant_cluster_ratio": round(float(ratios[dominant_idx]), 4),
        "dark_cluster_ratio": round(float(dark_ratio), 4),
        "green_cluster_ratio": round(float(green_ratio), 4),
        "red_cluster_ratio": round(float(red_ratio), 4),
        "ratios": [round(float(r), 4) for r in ratios.tolist()],
        "pixel_count": int(data.shape[0]),
    }


def _empty_result() -> dict:
    return {
        "n_clusters": 0,
        "dominant_cluster_index": -1,
        "dominant_cluster_ratio": 0.0,
        "dark_cluster_ratio": 0.0,
        "green_cluster_ratio": 0.0,
        "red_cluster_ratio": 0.0,
        "ratios": [],
        "pixel_count": 0,
    }
