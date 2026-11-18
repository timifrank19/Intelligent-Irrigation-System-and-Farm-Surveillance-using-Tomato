# =============================================================================
# FILE:      prepare_leaf_dataset.py
# LOCATION:  project root (Intelligent_Tomato_Farm/prepare_leaf_dataset.py)
# PURPOSE:   Prepare the tomato leaf dataset.
#
# EXPECTED INPUT:
#   datasets/tomato_leaf/  — contains the unzipped Roboflow export
#                            (data.yaml + train/valid/test with images+labels)
#
# WHAT IT DOES:
#   1. Verifies the Roboflow export integrity (images <-> labels).
#   2. Reads the REAL class names from data.yaml (no fabrication).
#   3. Rewrites data.yaml with absolute paths on this machine.
#   4. Reports class counts and any missing pairs.
#
# NOTES:
#   The class list is whatever Roboflow v60 declares. We do NOT hard-code.
#   If the dataset is not present, this script exits cleanly.
# =============================================================================

from __future__ import annotations
import os
import config
from data_handler import RoboflowExport


def main() -> None:
    root = config.DATASET_TOMATO_LEAF
    yaml_path = os.path.join(root, "data.yaml")

    if not os.path.isfile(yaml_path):
        print(f"[prepare_leaf] No data.yaml found in {root}.")
        print( "               Download and unzip the Roboflow export there first.")
        return

    print(f"[prepare_leaf] Inspecting {root}")
    exp = RoboflowExport(root)
    print(exp.summary())

    print("[prepare_leaf] Verification:")
    for split, stats in exp.verify().items():
        print(f"  {split}: {stats}")

    exp.rewrite_yaml_to_absolute()
    print(f"[prepare_leaf] Rewrote {yaml_path} with absolute paths.")
    print("[prepare_leaf] Done. Class names as declared by the dataset:")
    for i, name in enumerate(exp.class_names):
        print(f"  {i}: {name}")


if __name__ == "__main__":
    main()
