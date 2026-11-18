# =============================================================================
# FILE:      supervisor.py
# LOCATION:  Intelligent_Tomato_Farm/supervisor.py
# PURPOSE:   Neural evidence-fusion supervisor (14-class).
#
#            Loads three artifacts from models/supervisor/:
#              - supervisor.keras  (trained neural network)
#              - label_map.json    (class index → name)
#              - scaler.pkl        (StandardScaler for feature normalization)
#
#            Runs a rule-based healthy-leaf override BEFORE the neural model
#            (since the "Healthy" leaf class was excluded from training).
#
#            Falls back to a transparent rule-based fusion if the neural
#            model isn't available.
# =============================================================================

from __future__ import annotations
import json
import os
import pickle
import numpy as np

import config


# -----------------------------------------------------------------------------
# MODEL CACHE
# -----------------------------------------------------------------------------
_MODEL  = None
_LABELS = None
_SCALER = None


def _load_model():
    global _MODEL, _LABELS, _SCALER
    if _MODEL is not None:
        return

    if not os.path.isfile(config.SUPERVISOR_MODEL):
        return

    try:
        import tensorflow as tf
        _MODEL = tf.keras.models.load_model(config.SUPERVISOR_MODEL)
    except Exception as e:
        print(f"[supervisor] Could not load model: {e}")
        _MODEL = None
        return

    # Label map
    if os.path.isfile(config.SUPERVISOR_LABEL_MAP):
        try:
            with open(config.SUPERVISOR_LABEL_MAP, "r", encoding="utf-8") as f:
                _LABELS = json.load(f)
        except Exception as e:
            print(f"[supervisor] Could not load label_map: {e}")
            _LABELS = None

    # Scaler (critical — model expects normalized features)
    if os.path.isfile(config.SUPERVISOR_SCALER):
        try:
            with open(config.SUPERVISOR_SCALER, "rb") as f:
                _SCALER = pickle.load(f)
        except Exception as e:
            print(f"[supervisor] Could not load scaler: {e}")
            _SCALER = None
    else:
        print("[supervisor] WARNING: scaler.pkl not found — predictions will be unreliable")


# -----------------------------------------------------------------------------
# FEATURE BUILDER (must MATCH the Kaggle training cell exactly)
# -----------------------------------------------------------------------------
def _build_feature_vector(yolo_class, yolo_confidence, hsv, kmeans, edge, label_space):
    base = [
        float(yolo_confidence),
        float(hsv.get("green_pct", 0.0)),
        float(hsv.get("yellow_pct", 0.0)),
        float(hsv.get("brown_pct", 0.0)),
        float(hsv.get("dark_pct", 0.0)),
        float(hsv.get("abnormal_pct", 0.0)),
        float(kmeans.get("n_clusters", 0)),
        float(kmeans.get("dominant_cluster_ratio", 0.0)),
        float(kmeans.get("dark_cluster_ratio", 0.0)),
        float(edge.get("edge_density", 0.0)),
        float(edge.get("lesion_count", 0)),
        float(edge.get("mean_edge_length", 0.0)),
    ]
    oh = [0.0] * len(label_space)
    if yolo_class in label_space:
        oh[label_space.index(yolo_class)] = 1.0
    return np.asarray(base + oh, dtype=np.float32)


# -----------------------------------------------------------------------------
# RULE-BASED HEALTHY-LEAF OVERRIDE
# -----------------------------------------------------------------------------
def _looks_healthy(hsv: dict) -> bool:
    """Heuristic: very green, almost no abnormal pixels, almost no brown."""
    return (
        hsv.get("green_pct", 0) > 65
        and hsv.get("abnormal_pct", 0) < 15
        and hsv.get("brown_pct", 0) < 5
    )


# -----------------------------------------------------------------------------
# RULE-BASED FALLBACK (used when no trained model is available)
# -----------------------------------------------------------------------------
def _rule_based_fusion(yolo_class, yolo_confidence, hsv, kmeans, edge):
    score = {yolo_class: 0.55 * float(yolo_confidence)}

    if hsv.get("dark_pct", 0) > 25:
        score["Anthracnose"] = score.get("Anthracnose", 0.0) + 0.25
    if hsv.get("brown_pct", 0) > 20:
        score["Blossom end rot"] = score.get("Blossom end rot", 0.0) + 0.25
    if hsv.get("yellow_pct", 0) > 30:
        score["Spotted wilt Virus"] = score.get("Spotted wilt Virus", 0.0) + 0.20
    if hsv.get("green_pct", 0) > 60 and hsv.get("abnormal_pct", 0) < 15:
        score["Healthy Tomato"] = score.get("Healthy Tomato", 0.0) + 0.30

    if kmeans.get("dark_cluster_ratio", 0) > 0.30:
        score["Anthracnose"] = score.get("Anthracnose", 0.0) + 0.15
    if kmeans.get("green_cluster_ratio", 0) > 0.60:
        score["Healthy Tomato"] = score.get("Healthy Tomato", 0.0) + 0.15

    if edge.get("lesion_count", 0) >= 4:
        score["Bacterial_Spot"] = score.get("Bacterial_Spot", 0.0) + 0.20
    if edge.get("edge_density", 0) > 0.15:
        score["Bacterial_Spot"] = score.get("Bacterial_Spot", 0.0) + 0.10

    if not score:
        return {
            "primary": "unsure",
            "confidence": 0.0,
            "top3": [("unsure", 0.0)],
            "uncertain": True,
            "fallback": True,
        }

    ranked = sorted(score.items(), key=lambda kv: kv[1], reverse=True)
    top3 = ranked[:3]
    total = sum(v for _, v in ranked) or 1.0
    top3_norm = [(n, round(v / total, 4)) for n, v in top3]
    primary, primary_score = top3[0]
    primary_conf = round(primary_score / total, 4)

    uncertain = primary_conf < config.SUPERVISOR_UNCERTAIN_THRESHOLD or (
        len(top3) >= 2 and (top3[0][1] - top3[1][1]) / total < 0.15
    )

    return {
        "primary": primary,
        "confidence": primary_conf,
        "top3": top3_norm,
        "uncertain": bool(uncertain),
        "fallback": True,
    }


# -----------------------------------------------------------------------------
# PUBLIC API
# -----------------------------------------------------------------------------
def decide(yolo_class, yolo_confidence, hsv, kmeans, edge):
    # ---- Rule-based healthy override runs FIRST ----
    # The "Healthy" leaf class was excluded from supervisor training.
    # This heuristic catches clearly clean leaves before the neural model
    # has a chance to wrongly assign a disease label.
    if _looks_healthy(hsv):
        return {
            "primary": "Healthy (rule)",
            "confidence": 0.65,
            "top3": [("Healthy (rule)", 0.65)],
            "uncertain": False,
            "fallback": True,
        }

    _load_model()

    # ---- Rule-based fallback if model unavailable ----
    if _MODEL is None or _LABELS is None:
        return _rule_based_fusion(yolo_class, yolo_confidence, hsv, kmeans, edge)

    # ---- Neural supervisor ----
    try:
        x = _build_feature_vector(yolo_class, yolo_confidence, hsv, kmeans, edge, _LABELS)
        x = x.reshape(1, -1)

        # Normalize using the SAME scaler the model was trained with
        if _SCALER is not None:
            x = _SCALER.transform(x).astype(np.float32)

        probs = _MODEL.predict(x, verbose=0)[0]
        order = np.argsort(probs)[::-1]
        top3 = [(_LABELS[i], float(probs[i])) for i in order[:3]]
        primary, conf = top3[0]

        uncertain = conf < config.SUPERVISOR_UNCERTAIN_THRESHOLD or (
            len(top3) >= 2 and (top3[0][1] - top3[1][1]) < 0.10
        )

        return {
            "primary": primary,
            "confidence": round(float(conf), 4),
            "top3": [(n, round(float(p), 4)) for n, p in top3],
            "uncertain": bool(uncertain),
            "fallback": False,
        }
    except Exception as e:
        print(f"[supervisor] Model inference failed: {e}")
        return _rule_based_fusion(yolo_class, yolo_confidence, hsv, kmeans, edge)