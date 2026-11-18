# =============================================================================
# FILE:      prepare_fruit_dataset.py
# LOCATION:  project root (Intelligent_Tomato_Farm/prepare_fruit_dataset.py)
# PURPOSE:   Prepare the tomato fruit dataset.
#
# EXPECTED INPUT:
#   datasets/tomato_fruit/  — unzipped Roboflow export
#
# WHAT IT DOES:
#   Same steps as prepare_leaf_dataset.py, applied to the fruit dataset.
#   Reads the REAL class names from the dataset's own data.yaml.
# =============================================================================

from __future__ import annotations
import os
import config
from data_handler import RoboflowExport


def main() -> None:
    root = config.DATASET_TOMATO_FRUIT
    yaml_path = os.path.join(root, "data.yaml")

    if not os.path.isfile(yaml_path):
        print(f"[prepare_fruit] No data.yaml found in {root}.")
        print( "                Download and unzip the Roboflow export there first.")
        return

    print(f"[prepare_fruit] Inspecting {root}")
    exp = RoboflowExport(root)
    print(exp.summary())

    print("[prepare_fruit] Verification:")
    for split, stats in exp.verify().items():
        print(f"  {split}: {stats}")

    exp.rewrite_yaml_to_absolute()
    print(f"[prepare_fruit] Rewrote {yaml_path} with absolute paths.")
    print("[prepare_fruit] Done. Class names as declared by the dataset:")
    for i, name in enumerate(exp.class_names):
        print(f"  {i}: {name}")


if __name__ == "__main__":
    main()
