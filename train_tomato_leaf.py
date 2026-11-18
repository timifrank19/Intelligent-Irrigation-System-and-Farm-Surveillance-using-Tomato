# =============================================================================
# FILE:      train_tomato_leaf.py
# LOCATION:  project root (Intelligent_Tomato_Farm/train_tomato_leaf.py)
# PURPOSE:   Train the YOLOv8 tomato leaf disease detection model.
#
# READS:     datasets/tomato_leaf/data.yaml   (after prepare_leaf_dataset.py)
# WRITES:    models/tomato_leaf/tomato_leaf.pt
#            runs/train_tomato_leaf/...       (ultralytics logs)
#
# NOTES:
#   - Class list is read from the actual data.yaml. Nothing is hard-coded.
#   - If the data.yaml is missing, the script prints a clear message and exits.
# =============================================================================

from __future__ import annotations
import os
import shutil
import yaml
import config


DEFAULT_MODEL = "yolov8n.pt"
EPOCHS = 60
IMGSZ = 512
BATCH = 16
DEVICE = "0"   # use "cpu" if no GPU


def main() -> None:
    data_yaml = os.path.join(config.DATASET_TOMATO_LEAF, "data.yaml")
    if not os.path.isfile(data_yaml):
        print(f"[train_tomato_leaf] data.yaml not found: {data_yaml}")
        print( "                    Run prepare_leaf_dataset.py after unzipping the dataset.")
        return

    with open(data_yaml, "r", encoding="utf-8") as f:
        meta = yaml.safe_load(f)
    print(f"[train_tomato_leaf] Classes ({meta.get('nc')}): {meta.get('names')}")

    try:
        from ultralytics import YOLO
    except ImportError:
        print("[train_tomato_leaf] ultralytics is not installed. pip install ultralytics")
        return

    model = YOLO(DEFAULT_MODEL)
    results = model.train(
        data=data_yaml,
        epochs=EPOCHS,
        imgsz=IMGSZ,
        batch=BATCH,
        device=DEVICE,
        project=os.path.join(config.RUNS_DIR, "train_tomato_leaf"),
        name="run",
        exist_ok=True,
    )

    best = os.path.join(config.RUNS_DIR, "train_tomato_leaf", "run", "weights", "best.pt")
    if os.path.isfile(best):
        os.makedirs(config.TOMATO_LEAF_MODEL_DIR, exist_ok=True)
        shutil.copy2(best, config.TOMATO_LEAF_MODEL)
        print(f"[train_tomato_leaf] Saved model to {config.TOMATO_LEAF_MODEL}")
    else:
        print("[train_tomato_leaf] best.pt not found. Check training output.")


if __name__ == "__main__":
    main()
