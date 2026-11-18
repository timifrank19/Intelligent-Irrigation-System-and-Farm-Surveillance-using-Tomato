# =============================================================================
# FILE:      prepare_animal_dataset_night.py
# LOCATION:  project root (Intelligent_Tomato_Farm/prepare_animal_dataset_night.py)
# PURPOSE:   Prepare the thermal (night) animal dataset.
#
# EXPECTED INPUT:
#   datasets/animal/night/  — unzipped Roboflow export
#                             (animal_detection_flir_extra)
#
# WHAT IT DOES:
#   - Verifies integrity.
#   - Applies config.CLASS_RENAME_MAP.
#   - Drops non-farm classes listed in config.ANIMAL_NIGHT_DROP.
#   - Keeps only config.ANIMAL_NIGHT_CLASSES.
# =============================================================================

from __future__ import annotations
import os
import config
from data_handler import RoboflowExport, merge_exports


def main() -> None:
    root = config.DATASET_ANIMAL_NIGHT
    yaml_path = os.path.join(root, "data.yaml")

    if not os.path.isfile(yaml_path):
        print(f"[prepare_animal_night] No data.yaml found in {root}.")
        print( "                       Download and unzip the Roboflow export there first.")
        return

    print(f"[prepare_animal_night] Inspecting {root}")
    exp = RoboflowExport(root)
    print(exp.summary())

    merge_exports(
        sources=[exp],
        dest_root=root,
        rename_map=config.CLASS_RENAME_MAP,
        drop_classes=config.ANIMAL_NIGHT_DROP,
        keep_only=set(config.ANIMAL_NIGHT_CLASSES),
    )

    exp2 = RoboflowExport(root)
    exp2.rewrite_yaml_to_absolute()
    print(exp2.summary())
    for split, stats in exp2.verify().items():
        print(f"  {split}: {stats}")


if __name__ == "__main__":
    main()
