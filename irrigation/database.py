# =============================================================================
# FILE:      irrigation/database.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/database.py
# PURPOSE:   Single SQLite manager for the entire project.
#            Creates the irrigation tables AND the four new tables used by
#            surveillance, tomato analysis, and the supervisor learning pool.
#            All new tables are additive — nothing existing is modified.
# =============================================================================

from __future__ import annotations
import sqlite3
import pandas as pd
import numpy as np

from . import config as cfg


class DatabaseManager:
    def __init__(self, db_path: str = cfg.DB_FILE):
        self.db_path = db_path
        self._init_schema()

    # -------------------------------------------------------------------------
    # SCHEMA
    # -------------------------------------------------------------------------
    def _init_schema(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # ---- Existing irrigation tables -----------------------------------
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                soil_moisture REAL,
                temperature REAL,
                humidity REAL,
                vibration REAL,
                battery REAL,
                is_anomaly INTEGER DEFAULT 0,
                anomaly_type TEXT,
                pump_decision INTEGER DEFAULT 0,
                pump_confidence REAL DEFAULT 0,
                decision_reason TEXT,
                smart_schedule INTEGER DEFAULT 0,
                vibration_fault TEXT DEFAULT 'Normal',
                vibration_dominant_freq REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS decision_conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                hardware_decision INTEGER NOT NULL,
                backend_decision INTEGER NOT NULL,
                soil_moisture REAL,
                temperature REAL,
                humidity REAL,
                vibration REAL,
                battery REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dynamic_thresholds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parameter TEXT UNIQUE,
                min_threshold REAL,
                max_threshold REAL,
                updated_at TIMESTAMP,
                based_on_samples INTEGER
            )
        """)

        # ---- New tables for surveillance -----------------------------------
        cur.execute("""
            CREATE TABLE IF NOT EXISTS surveillance_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recording_id INTEGER,
                timestamp TEXT NOT NULL,
                frame_id INTEGER,
                class_name TEXT NOT NULL,
                confidence REAL NOT NULL,
                bbox_json TEXT,
                mode TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS surveillance_recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                filename TEXT NOT NULL,
                size INTEGER NOT NULL,
                duration_sec REAL,
                mode TEXT,
                event_count INTEGER DEFAULT 0,
                data BLOB NOT NULL,
                analyzed_at TEXT,
                deletion_at TEXT,
                notified_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ---- New tables for tomato results + supervisor pool ---------------
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tomato_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source_type TEXT,
                source_id INTEGER,
                yolo_class TEXT,
                yolo_confidence REAL,
                yolo_bbox_json TEXT,
                hsv_json TEXT,
                kmeans_json TEXT,
                edge_json TEXT,
                supervisor_primary TEXT,
                supervisor_confidence REAL,
                supervisor_top3_json TEXT,
                supervisor_uncertain INTEGER DEFAULT 0,
                recommendation_text TEXT,
                user_confirmed INTEGER DEFAULT 0,
                user_true_class TEXT,
                result_json_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS supervisor_training_pool (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                tomato_result_id INTEGER,
                yolo_class TEXT,
                yolo_confidence REAL,
                hsv_json TEXT,
                kmeans_json TEXT,
                edge_json TEXT,
                supervisor_primary TEXT,
                supervisor_confidence REAL,
                ground_truth TEXT,
                label_source TEXT,
                used_in_training INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ---- Default thresholds --------------------------------------------
        defaults = [
            ("soil_moisture", cfg.SOIL_DRY, cfg.SOIL_WET),
            ("temperature", cfg.TEMP_LOW, cfg.TEMP_HIGH),
            ("humidity", 50.0, 90.0),
            ("vibration", 0.05, 0.52),
            ("battery", 11.8, 13.6),
        ]
        for p, lo, hi in defaults:
            cur.execute("""
                INSERT OR IGNORE INTO dynamic_thresholds
                (parameter, min_threshold, max_threshold, based_on_samples)
                VALUES (?, ?, ?, 0)
            """, (p, lo, hi))

        conn.commit()
        conn.close()

    # -------------------------------------------------------------------------
    # IRRIGATION — existing API
    # -------------------------------------------------------------------------
    def add_reading(self, timestamp, soil_moisture, temperature, humidity,
                    vibration, battery, is_anomaly=0, anomaly_type=None,
                    pump_decision=0, pump_confidence=0, decision_reason="",
                    smart_schedule=0, vibration_fault="Normal",
                    vibration_dominant_freq=0):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO sensor_readings
            (timestamp, soil_moisture, temperature, humidity, vibration, battery,
             is_anomaly, anomaly_type, pump_decision, pump_confidence,
             decision_reason, smart_schedule, vibration_fault, vibration_dominant_freq)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, soil_moisture, temperature, humidity, vibration, battery,
              is_anomaly, anomaly_type, pump_decision, pump_confidence,
              decision_reason, smart_schedule, vibration_fault, vibration_dominant_freq))
        conn.commit()
        conn.close()

    def log_conflict(self, timestamp, hardware_decision, backend_decision,
                     soil_moisture, temperature, humidity, vibration, battery):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO decision_conflicts
            (timestamp, hardware_decision, backend_decision, soil_moisture,
             temperature, humidity, vibration, battery)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, hardware_decision, backend_decision, soil_moisture,
              temperature, humidity, vibration, battery))
        conn.commit()
        conn.close()

    def get_recent_readings(self, limit: int = 30) -> pd.DataFrame:
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql(f"""
            SELECT timestamp, soil_moisture, temperature, humidity, vibration,
                   battery, is_anomaly, anomaly_type, pump_decision,
                   pump_confidence, decision_reason, smart_schedule,
                   vibration_fault, vibration_dominant_freq
            FROM sensor_readings ORDER BY id DESC LIMIT {limit}
        """, conn)
        conn.close()
        return df

    def get_all_readings(self) -> pd.DataFrame:
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql("SELECT * FROM sensor_readings ORDER BY id ASC", conn)
        conn.close()
        return df

    def get_count(self) -> int:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sensor_readings")
        n = cur.fetchone()[0]
        conn.close()
        return int(n)

    def get_thresholds(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT parameter, min_threshold, max_threshold FROM dynamic_thresholds")
        rows = cur.fetchall()
        conn.close()
        return {r[0]: {"min": float(r[1]), "max": float(r[2])} for r in rows}

    def update_thresholds(self, parameter, min_val, max_val, samples):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO dynamic_thresholds
            (parameter, min_threshold, max_threshold, updated_at, based_on_samples)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (parameter, min_val, max_val, samples))
        conn.commit()
        conn.close()

    def update_dynamic_thresholds_from_data(self, df: pd.DataFrame) -> None:
        for param in ["soil_moisture", "temperature", "humidity", "vibration", "battery"]:
            if param in df.columns:
                vals = df[param].dropna().values
                if len(vals) >= 20:
                    lo = float(np.percentile(vals, 5) * 0.95)
                    hi = float(np.percentile(vals, 95) * 1.05)
                    self.update_thresholds(param, lo, hi, len(vals))

    # -------------------------------------------------------------------------
    # SURVEILLANCE — new API
    # -------------------------------------------------------------------------
    def insert_surveillance_event(self, recording_id, timestamp, frame_id,
                                  class_name, confidence, bbox_json,
                                  mode, source):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO surveillance_events
            (recording_id, timestamp, frame_id, class_name, confidence,
             bbox_json, mode, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (recording_id, timestamp, frame_id, class_name, confidence,
              bbox_json, mode, source))
        conn.commit()
        conn.close()

    def count_events_for_recording(self, recording_id: int) -> int:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM surveillance_events WHERE recording_id = ?",
                    (recording_id,))
        n = cur.fetchone()[0]
        conn.close()
        return int(n)

    def insert_recording(self, timestamp, filename, size, duration_sec,
                         mode, event_count, data: bytes):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO surveillance_recordings
            (timestamp, filename, size, duration_sec, mode, event_count, data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, filename, size, duration_sec, mode, event_count, data))
        conn.commit()
        rec_id = cur.lastrowid
        conn.close()
        return rec_id

    def get_recording(self, rec_id: int):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT * FROM surveillance_recordings WHERE id = ?", (rec_id,))
        row = cur.fetchone()
        cols = [d[0] for d in cur.description]
        conn.close()
        return dict(zip(cols, row)) if row else None

    def list_recordings(self, only_analyzed: bool = False):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        if only_analyzed:
            cur.execute("SELECT id, timestamp, filename, size, duration_sec, mode, "
                        "event_count, analyzed_at, deletion_at, notified_at "
                        "FROM surveillance_recordings WHERE analyzed_at IS NOT NULL "
                        "ORDER BY id DESC")
        else:
            cur.execute("SELECT id, timestamp, filename, size, duration_sec, mode, "
                        "event_count, analyzed_at, deletion_at, notified_at "
                        "FROM surveillance_recordings ORDER BY id DESC")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        conn.close()
        return [dict(zip(cols, r)) for r in rows]

    def mark_recording_analyzed(self, rec_id: int, deletion_at: str) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE surveillance_recordings
            SET analyzed_at = CURRENT_TIMESTAMP, deletion_at = ?
            WHERE id = ?
        """, (deletion_at, rec_id))
        conn.commit()
        conn.close()

    def mark_recording_notified(self, rec_id: int) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE surveillance_recordings SET notified_at = CURRENT_TIMESTAMP "
                     "WHERE id = ?", (rec_id,))
        conn.commit()
        conn.close()

    def delete_recording(self, rec_id: int) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM surveillance_recordings WHERE id = ?", (rec_id,))
        conn.commit()
        conn.close()

    # -------------------------------------------------------------------------
    # TOMATO RESULTS + SUPERVISOR POOL
    # -------------------------------------------------------------------------
    def insert_tomato_result(self, **kwargs) -> int:
        cols = [
            "timestamp", "source_type", "source_id", "yolo_class",
            "yolo_confidence", "yolo_bbox_json", "hsv_json", "kmeans_json",
            "edge_json", "supervisor_primary", "supervisor_confidence",
            "supervisor_top3_json", "supervisor_uncertain",
            "recommendation_text", "user_confirmed", "user_true_class",
            "result_json_path",
        ]
        vals = [kwargs.get(c) for c in cols]
        placeholders = ",".join(["?"] * len(cols))
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO tomato_results ({','.join(cols)}) VALUES ({placeholders})",
            vals,
        )
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return rid

    def insert_supervisor_pool_row(self, **kwargs) -> int:
        cols = [
            "timestamp", "tomato_result_id", "yolo_class", "yolo_confidence",
            "hsv_json", "kmeans_json", "edge_json", "supervisor_primary",
            "supervisor_confidence", "ground_truth", "label_source",
            "used_in_training",
        ]
        vals = [kwargs.get(c) for c in cols]
        placeholders = ",".join(["?"] * len(cols))
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO supervisor_training_pool ({','.join(cols)}) "
            f"VALUES ({placeholders})",
            vals,
        )
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return rid

    def get_tomato_results(self, limit: int = 100):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql(f"SELECT * FROM tomato_results ORDER BY id DESC LIMIT {limit}", conn)
        conn.close()
        return df

    def get_supervisor_pool(self, only_confirmed: bool = True):
        conn = sqlite3.connect(self.db_path)
        if only_confirmed:
            df = pd.read_sql(
                "SELECT * FROM supervisor_training_pool "
                "WHERE ground_truth IS NOT NULL AND ground_truth != '' "
                "AND used_in_training = 0 ORDER BY id ASC",
                conn,
            )
        else:
            df = pd.read_sql("SELECT * FROM supervisor_training_pool ORDER BY id ASC", conn)
        conn.close()
        return df

    def mark_pool_rows_used(self, ids):
        if not ids:
            return
        conn = sqlite3.connect(self.db_path)
        conn.executemany(
            "UPDATE supervisor_training_pool SET used_in_training = 1 WHERE id = ?",
            [(int(i),) for i in ids],
        )
        conn.commit()
        conn.close()


# Singleton used everywhere
db = DatabaseManager()
