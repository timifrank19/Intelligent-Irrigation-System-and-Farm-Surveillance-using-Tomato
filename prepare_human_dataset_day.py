# =============================================================================
# FILE:      prepare_human_dataset_day.py
# LOCATION:  project root (Intelligent_Tomato_Farm/prepare_human_dataset_day.py)
# PURPOSE:   Prepare the daytime human (RGB) dataset.
#
# EXPECTED INPUT:
#   datasets/human/day/  — unzipped Roboflow export
#                          (person-detection-in-daylight)
#
# WHAT IT DOES:
#   - Verifies integrity.
#   - Renames "Pedestrian" -> "person" via config.CLASS_RENAME_MAP.
#   - Rewrites data.yaml with absolute paths.
# =============================================================================

from __future__ import annotations
import os
import config
from data_handler import RoboflowExport, merge_exports


def main() -> None:
    root = config.DATASET_HUMAN_DAY
    yaml_path = os.path.join(root, "data.yaml")

    if not os.path.isfile(yaml_path):
        print(f"[prepare_human_day] No data.yaml found in {root}.")
        print( "                    Download and unzip the Roboflow export there first.")
        return

    print(f"[prepare_human_day] Inspecting {root}")
    exp = RoboflowExport(root)
    print(exp.summary())

    # Rename Pedestrian -> person and keep only "person"
    merge_exports(
        sources=[exp],
        dest_root=root,
        rename_map=config.CLASS_RENAME_MAP,
        drop_classes=set(),
        keep_only={"person"},
    )

    exp2 = RoboflowExport(root)
    exp2.rewrite_yaml_to_absolute()
    print(exp2.summary())
    for split, stats in exp2.verify().items():
        print(f"  {split}: {stats}")


if __name__ == "__main__":
    main()
