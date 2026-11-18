# =============================================================================
# FILE:      data_handler.py
# LOCATION:  project root (Intelligent_Tomato_Farm/data_handler.py)
# PURPOSE:   Modular, Roboflow-aware dataset utilities for all dataset
#            families in this project:
#               - tomato leaf        (single Roboflow YOLO export)
#               - tomato fruit       (single Roboflow YOLO export)
#               - human day          (single Roboflow YOLO export)
#               - human night        (single Roboflow YOLO export)
#               - animal day         (merge of two Roboflow YOLO exports)
#               - animal night       (single Roboflow YOLO export)
#
#            Responsibilities:
#               1. Inspect a Roboflow YOLO export.
#               2. Verify every image has a label and vice versa.
#               3. Read the REAL class names from data.yaml (no fabrication).
#               4. Rewrite data.yaml paths to absolute paths on this machine.
#               5. Merge multiple exports, applying class renaming and
#                  class dropping rules.
#               6. Never invent labels or bounding boxes.
# =============================================================================

from __future__ import annotations
import os
import shutil
import yaml
from typing import List, Dict, Tuple, Optional


# -----------------------------------------------------------------------------
# BASIC IO
# -----------------------------------------------------------------------------
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _list_images(folder: str) -> List[str]:
    if not os.path.isdir(folder):
        return []
    return sorted(
        f for f in os.listdir(folder)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTS
    )


def _read_yaml(path: str) -> Dict:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"data.yaml not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _write_yaml(path: str, data: Dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)


# -----------------------------------------------------------------------------
# ROBOLOFLOW EXPORT INSPECTION
# -----------------------------------------------------------------------------
class RoboflowExport:
    """
    Wraps a single Roboflow YOLOv8 export folder.
    Expected layout:
        root/
          data.yaml
          train/images/*.jpg   train/labels/*.txt
          valid/images/*.jpg   valid/labels/*.txt
          test/images/*.jpg    test/labels/*.txt   (may be missing)
    """

    def __init__(self, root: str):
        self.root = os.path.abspath(root)
        self.yaml_path = os.path.join(self.root, "data.yaml")
        self.raw_yaml = _read_yaml(self.yaml_path)
        self.class_names: List[str] = list(self.raw_yaml.get("names", []))
        self.nc: int = int(self.raw_yaml.get("nc", len(self.class_names)))
        self.splits: Dict[str, Tuple[str, str]] = {}

        for split in ("train", "valid", "test"):
            img_dir = os.path.join(self.root, split, "images")
            lbl_dir = os.path.join(self.root, split, "labels")
            if os.path.isdir(img_dir):
                self.splits[split] = (img_dir, lbl_dir)

    def summary(self) -> str:
        lines = [f"RoboflowExport: {self.root}"]
        lines.append(f"  nc    = {self.nc}")
        lines.append(f"  names = {self.class_names}")
        for split, (img_dir, _) in self.splits.items():
            lines.append(f"  {split}: {len(_list_images(img_dir))} images")
        return "\n".join(lines)

    def verify(self) -> Dict[str, Dict[str, int]]:
        """
        Verifies every image has a label and every label has an image.
        Returns counts. Never modifies anything.
        """
        report: Dict[str, Dict[str, int]] = {}
        for split, (img_dir, lbl_dir) in self.splits.items():
            imgs = _list_images(img_dir)
            lbls = []
            if os.path.isdir(lbl_dir):
                lbls = sorted(
                    f for f in os.listdir(lbl_dir)
                    if f.lower().endswith(".txt")
                )

            img_stems = {os.path.splitext(f)[0] for f in imgs}
            lbl_stems = {os.path.splitext(f)[0] for f in lbls}

            report[split] = {
                "images": len(imgs),
                "labels": len(lbls),
                "images_without_label": len(img_stems - lbl_stems),
                "labels_without_image": len(lbl_stems - img_stems),
            }
        return report

    def rewrite_yaml_to_absolute(self, out_path: Optional[str] = None) -> str:
        """
        Writes a data.yaml whose `path:` is the absolute root of this export
        and whose train/val/test entries are relative to that path.
        Returns the path to the written data.yaml.
        """
        out_path = out_path or self.yaml_path
        data = {
            "path": self.root,
            "train": "train/images",
            "val": "valid/images",
            "nc": self.nc,
            "names": self.class_names,
        }
        if "test" in self.splits:
            data["test"] = "test/images"
        _write_yaml(out_path, data)
        return out_path


# -----------------------------------------------------------------------------
# MERGING + CLASS CLEANING
# -----------------------------------------------------------------------------
def merge_exports(
    sources: List[RoboflowExport],
    dest_root: str,
    rename_map: Dict[str, str],
    drop_classes: set,
    keep_only: Optional[set] = None,
) -> str:
    """
    Merges multiple Roboflow YOLO exports into dest_root, applying:
      - class renaming via rename_map
      - dropping classes in drop_classes
      - optional keep_only whitelist (post-rename names)

    Writes a new data.yaml with the final class list.
    Does NOT fabricate annotations. Any label whose class is dropped is
    skipped; the image keeps whatever labels survive. If an image ends up
    with no labels after cleaning, it is skipped and reported.
    """
    dest_root = os.path.abspath(dest_root)
    os.makedirs(dest_root, exist_ok=True)

    final_classes: List[str] = []
    final_class_index: Dict[str, int] = {}

    for split in ("train", "valid", "test"):
        os.makedirs(os.path.join(dest_root, split, "images"), exist_ok=True)
        os.makedirs(os.path.join(dest_root, split, "labels"), exist_ok=True)

    skipped_empty = 0
    copied = 0

    for src in sources:
        for split, (img_dir, lbl_dir) in src.splits.items():
            for img_name in _list_images(img_dir):
                stem = os.path.splitext(img_name)[0]
                lbl_path = os.path.join(lbl_dir, stem + ".txt")
                if not os.path.isfile(lbl_path):
                    continue

                new_lines = []
                with open(lbl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) < 5:
                            continue
                        cls_id = int(float(parts[0]))
                        if cls_id < 0 or cls_id >= len(src.class_names):
                            continue
                        raw_name = src.class_names[cls_id]
                        mapped = rename_map.get(raw_name, raw_name)
                        if mapped in drop_classes:
                            continue
                        if keep_only is not None and mapped not in keep_only:
                            continue
                        if mapped not in final_class_index:
                            final_class_index[mapped] = len(final_classes)
                            final_classes.append(mapped)
                        new_id = final_class_index[mapped]
                        new_lines.append(f"{new_id} " + " ".join(parts[1:]))

                if not new_lines:
                    skipped_empty += 1
                    continue

                out_img = os.path.join(dest_root, split, "images", img_name)
                out_lbl = os.path.join(dest_root, split, "labels", stem + ".txt")
                if not os.path.exists(out_img):
                    shutil.copy2(os.path.join(img_dir, img_name), out_img)
                with open(out_lbl, "w", encoding="utf-8") as f:
                    f.write("\n".join(new_lines) + "\n")
                copied += 1

    data = {
        "path": dest_root,
        "train": "train/images",
        "val": "valid/images",
        "nc": len(final_classes),
        "names": final_classes,
    }
    if os.path.isdir(os.path.join(dest_root, "test", "images")):
        data["test"] = "test/images"

    _write_yaml(os.path.join(dest_root, "data.yaml"), data)

    print(f"[merge_exports] destination: {dest_root}")
    print(f"[merge_exports] copied      : {copied} images")
    print(f"[merge_exports] skipped     : {skipped_empty} images (no surviving labels)")
    print(f"[merge_exports] classes     : {final_classes}")
    return os.path.join(dest_root, "data.yaml")


# -----------------------------------------------------------------------------
# SIMPLE WRAPPERS FOR EACH DATASET
# -----------------------------------------------------------------------------
def inspect_single_export(root: str) -> RoboflowExport:
    exp = RoboflowExport(root)
    print(exp.summary())
    print("Verification:")
    for split, stats in exp.verify().items():
        print(f"  {split}: {stats}")
    exp.rewrite_yaml_to_absolute()
    print(f"Rewrote data.yaml at {exp.yaml_path}")
    return exp


def prepare_single_export(src_root: str, dest_root: str) -> str:
    """
    Copies a Roboflow export into a destination root (as-is), then
    rewrites the destination data.yaml to absolute paths.
    Used for leaf, fruit, human day, human night, animal night.
    """
    src_root = os.path.abspath(src_root)
    dest_root = os.path.abspath(dest_root)

    if not os.path.isdir(src_root):
        raise FileNotFoundError(f"Source dataset not found: {src_root}")

    if os.path.abspath(src_root) != os.path.abspath(dest_root):
        if os.path.isdir(dest_root):
            shutil.rmtree(dest_root)
        shutil.copytree(src_root, dest_root)

    exp = RoboflowExport(dest_root)
    exp.rewrite_yaml_to_absolute()
    print(exp.summary())
    for split, stats in exp.verify().items():
        print(f"  {split}: {stats}")
    return os.path.join(dest_root, "data.yaml")


# -----------------------------------------------------------------------------
# CLI (diagnostic only)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python data_handler.py <path-to-roboflow-export>")
        sys.exit(1)
    inspect_single_export(sys.argv[1])
