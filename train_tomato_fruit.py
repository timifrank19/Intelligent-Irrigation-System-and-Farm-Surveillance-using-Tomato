# =============================================================================
# FILE:      train_tomato_fruit.py
# LOCATION:  project root (Intelligent_Tomato_Farm/train_tomato_fruit.py)
# PURPOSE:   Train the YOLOv8 tomato fruit disease detection model.
#
# READS:     datasets/tomato_fruit/data.yaml
# WRITES:    models/tomato_fruit/tomato_fruit.pt
#            runs/train_tomato_fruit/...
# =============================================================================

from __future__ import annotations
import os
import shutil
import yaml
import config


DEFAULT_MODEL = "yolov8n.pt"
EPOCHS = 80
IMGSZ = 640
BATCH = 16
DEVICE = "0"


def main() -> None:
    data_yaml = os.path.join(config.DATASET_TOMATO_FRUIT, "data.yaml")
    if not os.path.isfile(data_yaml):
        print(f"[train_tomato_fruit] data.yaml not found: {data_yaml}")
        print( "                     Run prepare_fruit_dataset.py first.")
        return

    with open(data_yaml, "r", encoding="utf-8") as f:
        meta = yaml.safe_load(f)
    print(f"[train_tomato_fruit] Classes ({meta.get('nc')}): {meta.get('names')}")

    try:
        from ultralytics import YOLO
    except ImportError:
        print("[train_tomato_fruit] ultralytics is not installed.")
        return

    model = YOLO(DEFAULT_MODEL)
    model.train(
        data=data_yaml,
        epochs=EPOCHS,
        imgsz=IMGSZ,
        batch=BATCH,
        device=DEVICE,
        project=os.path.join(config.RUNS_DIR, "train_tomato_fruit"),
        name="run",
        exist_ok=True,
    )

    best = os.path.join(config.RUNS_DIR, "train_tomato_fruit", "run", "weights", "best.pt")
    if os.path.isfile(best):
        os.makedirs(config.TOMATO_FRUIT_MODEL_DIR, exist_ok=True)
        shutil.copy2(best, config.TOMATO_FRUIT_MODEL)
        print(f"[train_tomato_fruit] Saved model to {config.TOMATO_FRUIT_MODEL}")
    else:
        print("[train_tomato_fruit] best.pt not found.")


if __name__ == "__main__":
    main()
