# =============================================================================
# FILE:      tomato/results.py
# LOCATION:  Intelligent_Tomato_Farm/tomato/results.py
# PURPOSE:   Read helpers for tomato analysis results. Writes happen in
#            detection_memory.store so there is only one writer.
# =============================================================================

from __future__ import annotations
import json
import os
from typing import Optional

from irrigation.database import db
import config


def list_recent(limit: int = 50) -> list:
    df = db.get_tomato_results(limit=limit)
    if df is None or len(df) == 0:
        return []
    return df.to_dict(orient="records")


def get_result(result_id: int) -> Optional[dict]:
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM tomato_results WHERE id = ?", (result_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def load_json_for_result(result_id: int) -> Optional[dict]:
    """
    Loads the JSON file archived alongside the DB row, if present.
    """
    row = get_result(result_id)
    if not row:
        return None
    path = row.get("result_json_path")
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def confirm_result(result_id: int, is_correct: bool, true_class: Optional[str] = None) -> dict:
    """
    Admin feedback used by the supervisor reinforcement loop.
    - is_correct=True  -> ground_truth = supervisor_primary
    - is_correct=False -> ground_truth = true_class (must be provided)
    """
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT supervisor_primary FROM tomato_results WHERE id = ?", (result_id,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        return {"updated": False, "reason": "not_found"}

    if is_correct:
        ground_truth = row["supervisor_primary"]
        user_confirmed = 1
    else:
        ground_truth = true_class
        user_confirmed = 2

    conn.execute(
        "UPDATE tomato_results SET user_confirmed = ?, user_true_class = ? WHERE id = ?",
        (user_confirmed, ground_truth, result_id),
    )
    conn.execute(
        "UPDATE supervisor_training_pool SET ground_truth = ?, label_source = 'admin' "
        "WHERE tomato_result_id = ?",
        (ground_truth, result_id),
    )
    conn.commit()
    conn.close()
    return {"updated": True, "ground_truth": ground_truth}
