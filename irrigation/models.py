# =============================================================================
# FILE:      irrigation/models.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/models.py
# PURPOSE:   RandomForest irrigation decision model: training, loading,
#            auto-retrain. Logic preserved from S_Backend.py.
# =============================================================================

from __future__ import annotations
import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

from . import config as cfg
from . import state
from .database import db


def _build_features(df: pd.DataFrame):
    df = df.copy()
    df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
    df["minute"] = pd.to_datetime(df["timestamp"]).dt.minute
    df["time_of_day"] = df["hour"] + df["minute"] / 60
    df["soil_lag1"] = df["soil_moisture"].shift(1)
    df["temp_lag1"] = df["temperature"].shift(1)
    df["hum_lag1"] = df["humidity"].shift(1)
    df["vib_lag1"] = df["vibration"].shift(1)
    df["batt_lag1"] = df["battery"].shift(1)
    df["soil_roll3"] = df["soil_moisture"].rolling(3, min_periods=1).mean()
    df["temp_roll3"] = df["temperature"].rolling(3, min_periods=1).mean()
    df["is_schedule_time"] = df["hour"].apply(
        lambda h: 1 if (cfg.MORNING_START <= h <= cfg.MORNING_END)
        or (cfg.EVENING_START <= h <= cfg.EVENING_END) else 0
    )
    df = df.dropna().reset_index(drop=True)

    feature_cols = [
        "soil_moisture", "temperature", "humidity", "vibration", "battery",
        "hour", "time_of_day", "is_schedule_time",
        "soil_lag1", "temp_lag1", "hum_lag1", "vib_lag1", "batt_lag1",
        "soil_roll3", "temp_roll3",
    ]
    return df[feature_cols], df["pump_decision"]


def train_ai_model() -> bool:
    df = db.get_all_readings()
    if df is None or len(df) < 30:
        print("[irrigation.models] Not enough data to train (need >= 30).")
        return False

    X, y = _build_features(df)
    if len(X) < 30:
        print("[irrigation.models] Not enough usable rows after feature build.")
        return False

    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)

    model = RandomForestClassifier(
        n_estimators=100, max_depth=10, min_samples_split=5, random_state=42
    )
    model.fit(X_train_s, y_train)

    if len(X_test) > 0:
        y_pred = model.predict(scaler.transform(X_test))
        acc = accuracy_score(y_test, y_pred)
    else:
        acc = 0.85

    joblib.dump(model, cfg.MODELS_FILE)
    joblib.dump(scaler, cfg.SCALER_FILE)

    state.ai_model = model
    state.scaler = scaler
    state.model_accuracy = float(acc)
    state.last_trained_count = db.get_count()

    db.update_dynamic_thresholds_from_data(db.get_all_readings())
    print(f"[irrigation.models] Trained. Accuracy: {acc:.2%}")
    return True


def load_ai_model() -> bool:
    if os.path.exists(cfg.MODELS_FILE) and os.path.exists(cfg.SCALER_FILE):
        try:
            state.ai_model = joblib.load(cfg.MODELS_FILE)
            state.scaler = joblib.load(cfg.SCALER_FILE)
            state.model_accuracy = 0.0
            state.last_trained_count = db.get_count()
            print("[irrigation.models] Loaded existing AI model.")
            return True
        except Exception as e:
            print(f"[irrigation.models] Load failed: {e}")
            return False
    return False


def auto_retrain_if_needed() -> bool:
    if db.get_count() >= state.last_trained_count + cfg.RETRAIN_INTERVAL:
        print("[irrigation.models] Auto-retrain triggered.")
        return train_ai_model()
    return False
