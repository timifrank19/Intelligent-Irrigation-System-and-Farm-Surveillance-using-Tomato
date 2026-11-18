# =============================================================================
# FILE:      irrigation/config.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/config.py
# PURPOSE:   Irrigation-only constants. Mirrors the values from the original
#            S_Backend.py so behavior is unchanged.
# =============================================================================

from __future__ import annotations
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_FILE = os.path.join(PROJECT_ROOT, "irrigation.db")
MODELS_FILE = os.path.join(PROJECT_ROOT, "irrigation_model.pkl")
SCALER_FILE = os.path.join(PROJECT_ROOT, "scaler.pkl")
NN_FILE = os.path.join(PROJECT_ROOT, "nn_model.h5")

RETRAIN_INTERVAL = 100
ADMIN_PASSWORD = "IrrigationAdmin2024!"

MORNING_START = 5
MORNING_END = 8
EVENING_START = 17
EVENING_END = 20

SOIL_DRY = 0.30
SOIL_WET = 0.42
TEMP_HIGH = 32.0
TEMP_LOW = 22.0
BATTERY_CRITICAL = 20.0

FFT_SAMPLES = 256
FFT_SAMPLING_RATE = 500
