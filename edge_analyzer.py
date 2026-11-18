# =============================================================================
# FILE:      edge_analyzer.py
# LOCATION:  Intelligent_Tomato_Farm/edge_analyzer.py
# PURPOSE:   Independent edge/structure analysis of the same ROI.
#            Does NOT depend on HSV or K-means output.
# =============================================================================

from __future__ import annotations
import cv2
import numpy as np


def analyze_roi(roi_bgr: np.ndarray) -> dict:
    if roi_bgr is None or roi_bgr.size == 0:
        return _empty_result()

    gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(gray, 60, 140)

    edge_density = float(np.count_nonzero(edges)) / float(edges.size)

    # Contour analysis on the edge map -> lesion-like closed regions
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

    lesion_count = 0
    lengths = []
    areas = []
    for c in contours:
        a = cv2.contourArea(c)
        if a < 8:
            continue
        lesion_count += 1
        areas.append(float(a))
        lengths.append(float(cv2.arcLength(c, True)))

    mean_len = float(np.mean(lengths)) if lengths else 0.0
    mean_area = float(np.mean(areas)) if areas else 0.0
    max_area = float(np.max(areas)) if areas else 0.0

    # Laplacian variance => texture roughness
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    return {
        "edge_density": round(edge_density, 5),
        "lesion_count": int(lesion_count),
        "mean_edge_length": round(mean_len, 3),
        "mean_lesion_area": round(mean_area, 3),
        "max_lesion_area": round(max_area, 3),
        "laplacian_variance": round(lap_var, 3),
        "pixel_count": int(gray.size),
    }


def _empty_result() -> dict:
    return {
        "edge_density": 0.0,
        "lesion_count": 0,
        "mean_edge_length": 0.0,
        "mean_lesion_area": 0.0,
        "max_lesion_area": 0.0,
        "laplacian_variance": 0.0,
        "pixel_count": 0,
    }
