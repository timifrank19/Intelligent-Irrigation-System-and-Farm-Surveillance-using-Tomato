# =============================================================================
# FILE:      irrigation/routes/sensors.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/routes/sensors.py
# PURPOSE:   POST /api/sensor-data — receives sensor JSON from S_hardware.cpp
#            and runs the full irrigation decision pipeline.
#            Logic preserved from S_Backend.py.
# =============================================================================

from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter

from .. import config as cfg
from .. import state
from ..database import db
from ..models import auto_retrain_if_needed
from ..neural import predict_with_nn

router = APIRouter()


@router.post("/api/sensor-data")
async def receive_sensor_data(data: dict):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        soil = data.get("soil_moisture")
        temp = data.get("temperature")
        hum = data.get("humidity")
        vib = data.get("vibration")
        batt = data.get("battery")
        decision_hw = int(data.get("pump_decision", 0))
        reason = data.get("decision_reason", "From hardware")
        soil_fail = int(data.get("soil_sensor_failed", 0))
        temp_fail = int(data.get("temp_sensor_failed", 0))
        vib_fail = int(data.get("vibration_sensor_failed", 0))
        vib_fault = data.get("vibration_fault", "Normal")
        vib_dom = float(data.get("vibration_dominant_freq", 0))

        using_prediction = False
        missing = {
            "soil": soil is None,
            "temp": temp is None,
            "hum": hum is None,
            "vib": vib is None,
            "batt": batt is None,
        }

        if any(missing.values()):
            if missing["soil"]:
                soil = predict_with_nn(temp or 28.0, hum or 65.0,
                                       datetime.now().hour,
                                       datetime.now().weekday())
                using_prediction = True
            if missing["temp"]:
                temp = 28.0 + (0.35 - (soil or 0.35)) * 15
                using_prediction = True
            if missing["hum"]:
                hum = 65.0
                using_prediction = True
            if missing["vib"]:
                vib = 0.10
                using_prediction = True
            if missing["batt"]:
                batt = 12.5
                using_prediction = True

        if using_prediction:
            db.log_conflict(timestamp, decision_hw, decision_hw,
                            float(soil or 0.35), float(temp or 28.0),
                            float(hum or 65.0), float(vib or 0.10),
                            float(batt or 12.5))
            final_decision = decision_hw
            decision_reason = "Hardware wins (NN predicted)"
        else:
            final_decision = decision_hw
            decision_reason = reason

        is_anomaly = 0
        anomaly_type = None
        if soil_fail or temp_fail or vib_fail:
            is_anomaly = 1
            anomaly_type = "sensor_failure"
        if vib is not None and (vib < 0 or vib > 2.0):
            is_anomaly = 1
            anomaly_type = "vibration_sensor_fault"

        hour = datetime.now().hour
        is_schedule = 1 if (cfg.MORNING_START <= hour <= cfg.MORNING_END) or \
                          (cfg.EVENING_START <= hour <= cfg.EVENING_END) else 0

        db.add_reading(
            timestamp=timestamp,
            soil_moisture=round(float(soil or 0.35), 3),
            temperature=round(float(temp or 28.0), 1),
            humidity=round(float(hum or 65.0), 1),
            vibration=round(float(vib or 0.10), 3),
            battery=round(float(batt or 12.5), 1),
            is_anomaly=is_anomaly,
            anomaly_type=anomaly_type,
            pump_decision=final_decision,
            pump_confidence=85 if final_decision == 1 else 80,
            decision_reason=decision_reason,
            smart_schedule=is_schedule,
            vibration_fault=vib_fault,
            vibration_dominant_freq=vib_dom,
        )

        state.pump_status = (final_decision == 1)
        auto_retrain_if_needed()

        th = db.get_thresholds()
        return {
            "status": "ok",
            "soil_dry_threshold": th.get("soil_moisture", {}).get("min", cfg.SOIL_DRY),
            "temp_high_threshold": th.get("temperature", {}).get("max", cfg.TEMP_HIGH),
            "vibration_threshold": th.get("vibration", {}).get("max", 0.52),
            "pump_decision": final_decision,
            "using_prediction": using_prediction,
            "vibration_fault": vib_fault,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
