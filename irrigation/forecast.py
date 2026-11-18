# =============================================================================
# FILE:      irrigation/forecast.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/forecast.py
# PURPOSE:   Exponential Smoothing forecast logic used by /api/forecast.
# =============================================================================

from __future__ import annotations
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from .database import db


def _forecast_param(values, steps=6):
    if len(values) < 10:
        return None, None
    try:
        model = ExponentialSmoothing(
            np.asarray(values, dtype=float),
            trend="add", seasonal=None,
            initialization_method="estimated",
        )
        fit = model.fit()
        fc = fit.forecast(steps)
        resid = fit.resid
        if np.mean(values) > 0:
            conf = max(50, min(95, 100 - (np.std(resid) / np.mean(values) * 50)))
        else:
            conf = 70.0
        return fc, float(conf)
    except Exception:
        return None, None


def build_forecast(limit: int = 50) -> dict:
    df = db.get_recent_readings(limit=limit)
    if len(df) < 10:
        return {"error": "Not enough data for forecast"}

    soil = df["soil_moisture"].values[::-1]
    temp = df["temperature"].values[::-1]
    hum = df["humidity"].values[::-1]

    soil_fc, soil_c = _forecast_param(soil, 6)
    temp_fc, temp_c = _forecast_param(temp, 6)
    hum_fc, hum_c = _forecast_param(hum, 6)

    soil_min = db.get_thresholds().get("soil_moisture", {}).get("min", 0.30)

    irrigation_needed = False
    irrigation_time = None
    if soil_fc is not None:
        for i, v in enumerate(soil_fc):
            if v < soil_min:
                irrigation_needed = True
                irrigation_time = i + 1
                break

    return {
        "soil_forecast": soil_fc.tolist() if soil_fc is not None else None,
        "soil_confidence": soil_c,
        "temp_forecast": temp_fc.tolist() if temp_fc is not None else None,
        "temp_confidence": temp_c,
        "hum_forecast": hum_fc.tolist() if hum_fc is not None else None,
        "hum_confidence": hum_c,
        "irrigation_needed": irrigation_needed,
        "irrigation_time": irrigation_time,
    }
