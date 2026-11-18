# =============================================================================
# FILE:      prepare_animal_dataset_day.py
# LOCATION:  project root (Intelligent_Tomato_Farm/prepare_animal_dataset_day.py)
# PURPOSE:   Prepare the daytime (RGB) animal dataset by merging two
#            Roboflow exports and applying the approved class cleaning.
#
# EXPECTED INPUT:
#   datasets/animal/day/
#       farm_animals/         <- unzip farm-animals-yrpj3 here
#       animal_detection/     <- unzip animal-detection-yolov8 here
#
# WHAT IT DOES:
#   - Reads each export's data.yaml.
#   - Applies config.CLASS_RENAME_MAP (e.g. cattle -> cow, Pedestrian -> person).
#   - Drops config.ANIMAL_DAY_DROP (junk / non-farm classes).
#   - Merges into datasets/animal/day/merged/ with a new data.yaml.
# =============================================================================

from __future__ import annotations
import os
import config
from data_handler import RoboflowExport, merge_exports


def _locate_export(parent: str) -> str:
    """Return the first folder under parent that has a data.yaml."""
    if not os.path.isdir(parent):
        return ""
    for name in sorted(os.listdir(parent)):
        candidate = os.path.join(parent, name)
        if os.path.isfile(os.path.join(candidate, "data.yaml")):
            return candidate
    return ""


def main() -> None:
    base = config.DATASET_ANIMAL_DAY
    farm_dir = os.path.join(base, "farm_animals")
    animal_dir = os.path.join(base, "animal_detection")

    sources = []
    for label, folder in (("farm_animals", farm_dir), ("animal_detection", animal_dir)):
        found = folder if os.path.isfile(os.path.join(folder, "data.yaml")) else _locate_export(folder)
        if not found:
            print(f"[prepare_animal_day] Missing export: {folder}")
            print( "                     Unzip the Roboflow dataset there first.")
            return
        exp = RoboflowExport(found)
        print(f"[prepare_animal_day] Loaded {label}: {found}")
        print(exp.summary())
        sources.append(exp)

    dest = os.path.join(base, "merged")
    merge_exports(
        sources=sources,
        dest_root=dest,
        rename_map=config.CLASS_RENAME_MAP,
        drop_classes=config.ANIMAL_DAY_DROP,
        keep_only=set(config.ANIMAL_DAY_CLASSES),
    )

    merged = RoboflowExport(dest)
    merged.rewrite_yaml_to_absolute()
    print(merged.summary())
    for split, stats in merged.verify().items():
        print(f"  {split}: {stats}")


if __name__ == "__main__":
    main()
