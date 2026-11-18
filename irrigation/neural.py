# =============================================================================
# FILE:      irrigation/neural.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/neural.py
# PURPOSE:   Neural-network fallback used when sensor values are missing.
#            Preserved from S_Backend.py.
# =============================================================================

from __future__ import annotations
import os
import numpy as np
import pandas as pd

from . import config as cfg
from . import state
from .database import db


def _build_model():
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense
    m = Sequential([
        Dense(16, activation="relu", input_shape=(4,)),
        Dense(8, activation="relu"),
        Dense(1, activation="sigmoid"),
    ])
    m.compile(optimizer="adam", loss="mse", metrics=["mae"])
    return m


def train_neural_network() -> bool:
    df = db.get_all_readings()
    if df is None or len(df) < 100:
        print("[irrigation.neural] Not enough data (need >= 100). Skipping.")
        return False

    df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
    df["day_of_week"] = pd.to_datetime(df["timestamp"]).dt.dayofweek
    X = df[["temperature", "humidity", "hour", "day_of_week"]].values
    y = df["soil_moisture"].values

    x_mean = X.mean(axis=0)
    x_std = X.std(axis=0) + 1e-8
    Xn = (X - x_mean) / x_std

    model = _build_model()
    model.fit(Xn, y, epochs=50, batch_size=16, verbose=0)
    try:
        model.save(cfg.NN_FILE)
    except Exception as e:
        print(f"[irrigation.neural] Save failed: {e}")

    state.nn_model = model
    state.nn_trained = True
    print("[irrigation.neural] Trained successfully.")
    return True


def predict_with_nn(temperature, humidity, hour, day_of_week) -> float:
    if not state.nn_trained or state.nn_model is None:
        return 0.35
    try:
        x_mean = np.array([28.0, 65.0, 12.0, 3.0])
        x_std = np.array([5.0, 15.0, 7.0, 2.0])
        xn = (np.array([[temperature, humidity, hour, day_of_week]]) - x_mean) / x_std
        pred = state.nn_model.predict(xn, verbose=0)[0][0]
        return float(max(0.15, min(0.55, pred)))
    except Exception:
        return 0.35
