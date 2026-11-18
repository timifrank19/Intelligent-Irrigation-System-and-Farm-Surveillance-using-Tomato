# =============================================================================
# FILE:      hsv_analyzer.py
# LOCATION:  Intelligent_Tomato_Farm/hsv_analyzer.py
# PURPOSE:   Independent HSV analysis of a tomato leaf/fruit ROI.
#            Produces measurable colour statistics ONLY. It does NOT
#            diagnose disease on its own.
# =============================================================================

from __future__ import annotations
import cv2
import numpy as np


def analyze_roi(roi_bgr: np.ndarray) -> dict:
    """
    Args:
        roi_bgr: BGR crop of the YOLO ROI (numpy uint8 array)
    Returns:
        dict with green / yellow / brown / dark / abnormal percentages and
        a few raw HSV statistics.
    """
    if roi_bgr is None or roi_bgr.size == 0:
        return _empty_result()

    hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    total = float(h.size)

    # --- colour masks ------------------------------------------------------
    # green
    green = cv2.inRange(hsv, (35, 40, 40), (85, 255, 255))
    # yellow
    yellow = cv2.inRange(hsv, (20, 60, 80), (35, 255, 255))
    # brown (orange-brown hue, low value)
    brown = cv2.inRange(hsv, (5, 60, 30), (20, 220, 180))
    # dark areas (very low value)
    dark = cv2.inRange(hsv, (0, 0, 0), (180, 255, 60))
    # red (ripe fruit or lesions)
    red1 = cv2.inRange(hsv, (0, 70, 50), (10, 255, 255))
    red2 = cv2.inRange(hsv, (170, 70, 50), (180, 255, 255))
    red = cv2.bitwise_or(red1, red2)

    green_pct = float(np.count_nonzero(green)) / total * 100
    yellow_pct = float(np.count_nonzero(yellow)) / total * 100
    brown_pct = float(np.count_nonzero(brown)) / total * 100
    dark_pct = float(np.count_nonzero(dark)) / total * 100
    red_pct = float(np.count_nonzero(red)) / total * 100

    # abnormal = anything not green and not healthy red
    abnormal_pct = max(0.0, 100.0 - green_pct - red_pct)

    return {
        "green_pct": round(green_pct, 2),
        "yellow_pct": round(yellow_pct, 2),
        "brown_pct": round(brown_pct, 2),
        "dark_pct": round(dark_pct, 2),
        "red_pct": round(red_pct, 2),
        "abnormal_pct": round(abnormal_pct, 2),
        "hue_mean": round(float(np.mean(h)), 2),
        "hue_std": round(float(np.std(h)), 2),
        "sat_mean": round(float(np.mean(s)), 2),
        "val_mean": round(float(np.mean(v)), 2),
        "pixel_count": int(total),
    }


def _empty_result() -> dict:
    return {
        "green_pct": 0.0, "yellow_pct": 0.0, "brown_pct": 0.0,
        "dark_pct": 0.0, "red_pct": 0.0, "abnormal_pct": 0.0,
        "hue_mean": 0.0, "hue_std": 0.0,
        "sat_mean": 0.0, "val_mean": 0.0,
        "pixel_count": 0,
    }
