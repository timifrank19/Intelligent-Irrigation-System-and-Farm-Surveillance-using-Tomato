# =============================================================================
# FILE:      train_animal_night.py
# LOCATION:  project root (Intelligent_Tomato_Farm/train_animal_night.py)
# PURPOSE:   Train the thermal (night) animal detection YOLOv8 model.
#
# READS:     datasets/animal/night/data.yaml
# WRITES:    models/human_animal/animal_night.pt
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
    data_yaml = os.path.join(config.DATASET_ANIMAL_NIGHT, "data.yaml")
    if not os.path.isfile(data_yaml):
        print(f"[train_animal_night] data.yaml not found: {data_yaml}")
        print( "                     Run prepare_animal_dataset_night.py first.")
        return

    with open(data_yaml, "r", encoding="utf-8") as f:
        meta = yaml.safe_load(f)
    print(f"[train_animal_night] Classes ({meta.get('nc')}): {meta.get('names')}")

    from ultralytics import YOLO
    model = YOLO(DEFAULT_MODEL)
    model.train(
        data=data_yaml, epochs=EPOCHS, imgsz=IMGSZ, batch=BATCH, device=DEVICE,
        project=os.path.join(config.RUNS_DIR, "train_animal_night"),
        name="run", exist_ok=True,
    )
    best = os.path.join(config.RUNS_DIR, "train_animal_night", "run", "weights", "best.pt")
    if os.path.isfile(best):
        shutil.copy2(best, config.ANIMAL_NIGHT_MODEL)
        print(f"[train_animal_night] Saved to {config.ANIMAL_NIGHT_MODEL}")


if __name__ == "__main__":
    main()
