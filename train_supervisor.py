# =============================================================================
# FILE: train_supervisor.py
# PURPOSE: Train the 14-class neural evidence-fusion supervisor.
# =============================================================================
# train_supervisor.py — auto-detects label space from the .pt models
from __future__ import annotations
import json, os
import numpy as np
import config
from detection_memory.retrain_data import export_training_rows

MIN_ROWS = 300
MIN_PER_CLASS = 10


def _get_model_classes(model_path):
    if not os.path.isfile(model_path):
        print(f"[train_supervisor] WARNING: model not found at {model_path}")
        return []
    try:
        from ultralytics import YOLO
        m = YOLO(model_path)
        return [m.names[i] for i in sorted(m.names)]
    except Exception as e:
        print(f"[train_supervisor] WARNING: could not load {model_path}: {e}")
        return []


def _build_label_space():
    leaf = _get_model_classes(os.path.join(config.MODELS_DIR, "tomato_leaf", "tomato_leaf.pt"))
    fruit = _get_model_classes(os.path.join(config.MODELS_DIR, "tomato_fruit", "tomato_fruit.pt"))
    if not leaf:
        leaf = list(config.TOMATO_LEAF_EXPECTED_CLASSES)
    if not fruit:
        fruit = list(config.TOMATO_FRUIT_EXPECTED_CLASSES)
    space = []
    for n in fruit + leaf:
        if n not in space:
            space.append(n)
    print(f"[train_supervisor] Label space ({len(space)} classes):")
    for i, n in enumerate(space):
        print(f"  {i:2d}  {n}")
    return space


def main():
    print("[train_supervisor] Loading training pool...")
    feats, yolo_classes, row_ids = export_training_rows(only_confirmed=True)

    if feats.shape[0] < MIN_ROWS:
        print(f"[train_supervisor] Only {feats.shape[0]} confirmed rows. Need >= {MIN_ROWS}.")
        return

    label_space = _build_label_space()
    if not label_space:
        print("[train_supervisor] No label space available. Aborting.")
        return

    label_index = {name: i for i, name in enumerate(label_space)}
    print(f"[train_supervisor] Rows: {feats.shape[0]}  Classes: {len(label_space)}")

    oh = np.zeros((len(yolo_classes), len(label_space)), dtype=np.float32)
    for i, c in enumerate(yolo_classes):
        if c in label_index:
            oh[i, label_index[c]] = 1.0
        else:
            print(f"[warn] unknown YOLO class '{c}' — zero one-hot")

    X = np.concatenate([feats, oh], axis=1)

    from irrigation.database import db
    df = db.get_supervisor_pool(only_confirmed=True)
    y_names = df["ground_truth"].tolist()
    y = np.array([label_index.get(n, -1) for n in y_names], dtype=np.int64)

    valid = y >= 0
    dropped = len(y) - valid.sum()
    if dropped:
        print(f"[train_supervisor] Dropped {dropped} rows with unknown ground_truth")
    X, y = X[valid], y[valid]

    counts = np.bincount(y, minlength=len(label_space))
    print("\n[train_supervisor] Per-class counts:")
    for i, n in enumerate(counts):
        print(f"  {i:2d}  {label_space[i]:28s} {n}")

    present = (counts > 0).sum()
    if present < 2:
        print(f"[train_supervisor] Only {present} class(es) present — cannot train.")
        return

    try:
        import tensorflow as tf
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Dense, Dropout
    except ImportError:
        print("[train_supervisor] tensorflow not installed. Run: pip install tensorflow")
        return

    model = Sequential([
        Dense(128, activation="relu", input_shape=(X.shape[1],)),
        Dropout(0.3),
        Dense(64, activation="relu"),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(len(label_space), activation="softmax"),
    ])
    model.compile(optimizer="adam",
                  loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])

    history = model.fit(X, y, epochs=80, batch_size=16,
                        verbose=1, validation_split=0.2)

    os.makedirs(config.SUPERVISOR_MODEL_DIR, exist_ok=True)
    model.save(os.path.join(config.SUPERVISOR_MODEL_DIR, "supervisor.pt"))

    with open(os.path.join(config.SUPERVISOR_MODEL_DIR, "label_map.json"), "w") as f:
        json.dump(label_space, f, indent=2)

    val_acc = history.history["val_accuracy"][-1]
    print(f"\n[train_supervisor] Final val_accuracy: {val_acc:.3f}")
    print(f"[train_supervisor] Saved: {config.SUPERVISOR_MODEL_DIR}")

    from detection_memory.retrain_data import mark_rows_used
    mark_rows_used(row_ids)


if __name__ == "__main__":
    main()