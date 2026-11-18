# =============================================================================
# FILE:      train_human_day.py
# LOCATION:  project root (Intelligent_Tomato_Farm/train_human_day.py)
# PURPOSE:   Train the daytime (RGB) human detection YOLOv8 model.
#
# READS:     datasets/human/day/data.yaml
# WRITES:    models/human_animal/human_day.pt
# =============================================================================

from __future__ import annotations
import os
import shutil
import yaml
import config


DEFAULT_MODEL = "yolov8n.pt"
EPOCHS = 60
IMGSZ = 640
BATCH = 16
DEVICE = "0"


def main() -> None:
    data_yaml = os.path.join(config.DATASET_HUMAN_DAY, "data.yaml")
    if not os.path.isfile(data_yaml):
        print(f"[train_human_day] data.yaml not found: {data_yaml}")
        return

    with open(data_yaml, "r", encoding="utf-8") as f:
        meta = yaml.safe_load(f)
    print(f"[train_human_day] Classes: {meta.get('names')}")

    from ultralytics import YOLO
    model = YOLO(DEFAULT_MODEL)
    model.train(
        data=data_yaml, epochs=EPOCHS, imgsz=IMGSZ, batch=BATCH, device=DEVICE,
        project=os.path.join(config.RUNS_DIR, "train_human_day"),
        name="run", exist_ok=True,
    )
    best = os.path.join(config.RUNS_DIR, "train_human_day", "run", "weights", "best.pt")
    if os.path.isfile(best):
        shutil.copy2(best, config.HUMAN_DAY_MODEL)
        print(f"[train_human_day] Saved to {config.HUMAN_DAY_MODEL}")


if __name__ == "__main__":
    main()
