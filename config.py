# =============================================================================
# FILE:      config.py
# LOCATION:  project root (Intelligent_Tomato_Farm/config.py)
# PURPOSE:   Single source of truth for paths, class lists, thresholds,
#            retention rules, admin password, camera modes, and dataset
#            locations used across the entire project.
# =============================================================================

from __future__ import annotations
import os


# -----------------------------------------------------------------------------
# PROJECT ROOT
# -----------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


# -----------------------------------------------------------------------------
# DATABASE (single SQLite file used by the entire project)
# -----------------------------------------------------------------------------
DB_FILE = os.path.join(PROJECT_ROOT, "irrigation.db")


# -----------------------------------------------------------------------------
# ADMIN / SECURITY
# -----------------------------------------------------------------------------
ADMIN_PASSWORD = "IrrigationAdmin2024!"
ADMIN_HEADER = "X-Admin-Key"


# -----------------------------------------------------------------------------
# SERVER
# -----------------------------------------------------------------------------
HOST = "0.0.0.0"
PORT = 8000


# -----------------------------------------------------------------------------
# FRONTEND
# -----------------------------------------------------------------------------
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
FRONTEND_INDEX = os.path.join(FRONTEND_DIR, "index.html")


# -----------------------------------------------------------------------------
# RESULTS / RUNS
# -----------------------------------------------------------------------------
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
RUNS_DIR = os.path.join(PROJECT_ROOT, "runs")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(RUNS_DIR, exist_ok=True)


# -----------------------------------------------------------------------------
# MODELS
# -----------------------------------------------------------------------------
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

HUMAN_ANIMAL_MODEL_DIR = os.path.join(MODELS_DIR, "human_animal")
HUMAN_DAY_MODEL = os.path.join(HUMAN_ANIMAL_MODEL_DIR, "human_day.pt")
HUMAN_NIGHT_MODEL = os.path.join(HUMAN_ANIMAL_MODEL_DIR, "human_night.pt")
ANIMAL_DAY_MODEL = os.path.join(HUMAN_ANIMAL_MODEL_DIR, "animal_day.pt")
ANIMAL_NIGHT_MODEL = os.path.join(HUMAN_ANIMAL_MODEL_DIR, "animal_night.pt")

TOMATO_LEAF_MODEL_DIR = os.path.join(MODELS_DIR, "tomato_leaf")
TOMATO_LEAF_MODEL = os.path.join(TOMATO_LEAF_MODEL_DIR, "tomato_leaf.pt")

TOMATO_FRUIT_MODEL_DIR = os.path.join(MODELS_DIR, "tomato_fruit")
TOMATO_FRUIT_MODEL = os.path.join(TOMATO_FRUIT_MODEL_DIR, "tomato_fruit.pt")

SUPERVISOR_MODEL_DIR = os.path.join(MODELS_DIR, "supervisor")
SUPERVISOR_MODEL     = os.path.join(SUPERVISOR_MODEL_DIR, "supervisor.keras")   # .keras, not .pt
SUPERVISOR_LABEL_MAP = os.path.join(SUPERVISOR_MODEL_DIR, "label_map.json")
SUPERVISOR_SCALER    = os.path.join(SUPERVISOR_MODEL_DIR, "scaler.pkl")
SUPERVISOR_UNCERTAIN_THRESHOLD = 0.55

for d in (
    HUMAN_ANIMAL_MODEL_DIR,
    TOMATO_LEAF_MODEL_DIR,
    TOMATO_FRUIT_MODEL_DIR,
    SUPERVISOR_MODEL_DIR,
):
    os.makedirs(d, exist_ok=True)


# -----------------------------------------------------------------------------
# DATASETS
# -----------------------------------------------------------------------------
DATASETS_DIR = os.path.join(PROJECT_ROOT, "datasets")

DATASET_TOMATO_LEAF = os.path.join(DATASETS_DIR, "tomato_leaf")
DATASET_TOMATO_FRUIT = os.path.join(DATASETS_DIR, "tomato_fruit")
DATASET_HUMAN_DAY = os.path.join(DATASETS_DIR, "human", "day")
DATASET_HUMAN_NIGHT = os.path.join(DATASETS_DIR, "human", "night")
DATASET_ANIMAL_DAY = os.path.join(DATASETS_DIR, "animal", "day")
DATASET_ANIMAL_NIGHT = os.path.join(DATASETS_DIR, "animal", "night")

for d in (
    DATASET_TOMATO_LEAF,
    DATASET_TOMATO_FRUIT,
    DATASET_HUMAN_DAY,
    DATASET_HUMAN_NIGHT,
    DATASET_ANIMAL_DAY,
    DATASET_ANIMAL_NIGHT,
):
    os.makedirs(d, exist_ok=True)


# -----------------------------------------------------------------------------
# TOMATO CLASSES
# -----------------------------------------------------------------------------
# Fruit classes — read the REAL names from the trained data.yaml after
# preparation. This list is only the expected set; the code always
# prefers the dataset's own names.
TOMATO_FRUIT_EXPECTED_CLASSES = [
    "Anthracnose",
    "Bacterial_Spot",
    "Blossom end rot",
    "Healthy Tomato",
    "Spotted wilt Virus",
]

# Leaf classes — read the REAL names from the dataset data.yaml.
# Not hard-coded here because v60's class list is confirmed at prepare time.
TOMATO_LEAF_EXPECTED_CLASSES = [
    'Bacterial Spot',
    'Early Blight',
    'Healthy',
    'Late Blight',
    'Leaf Mold',
    'Septoria Leaf Spot',
    'Spider Mites',
    'Target Spot',
    'Yellow Leaf Curl Virus',
]



# -----------------------------------------------------------------------------
# HUMAN / ANIMAL CLASSES
# -----------------------------------------------------------------------------
HUMAN_DAY_CLASSES = ["person"]
HUMAN_NIGHT_CLASSES = ["person"]

# Day animal: merged from farm-animals-yrpj3 + animal-detection-yolov8,
# after class cleaning + renaming.
ANIMAL_DAY_CLASSES = [
    "cow",
    "dog",
    "goat",
    "sheep",
    "horse",
    "pig",
    "chicken",
    "duck",
    "donkey",
    "llama",
    "turkey",
    "peacock",
    "person",
]

# Night animal: from animal_detection_flir_extra, farm-relevant subset only.
ANIMAL_NIGHT_CLASSES = [
    "cow",
    "dog",
    "goat",
]


# -----------------------------------------------------------------------------
# CLASS CLEANING RULES (used by prepare_* scripts)
# -----------------------------------------------------------------------------
# Rename table applied to raw Roboflow class names.
CLASS_RENAME_MAP = {
    "Pedestrian": "person",
    "cattle": "cow",
    "Cattle": "cow",
    "Cow": "cow",
    "Dog": "dog",
    "Goat": "goat",
    "Sheep": "sheep",
    "Horse": "horse",
    "Pig": "pig",
    "Chicken": "chicken",
    "Duck": "duck",
    "Donkey": "donkey",
    "Llama": "llama",
    "Turkey": "turkey",
    "Peacock": "peacock",
}

# Classes to drop from the day animal merge.
ANIMAL_DAY_DROP = {
    "apple", "bean", "Balls", "bunny", "cute", "rat",
    "tiger", "lion", "leopard", "elephant", "standpig",
    "Tikus", "cpw", "ow", "shee[", "human",
}

# Classes to drop from the night animal model.
ANIMAL_NIGHT_DROP = {
    "elephant", "bear", "deer", "fox", "wild-boar",
}


# -----------------------------------------------------------------------------
# INFERENCE THRESHOLDS
# -----------------------------------------------------------------------------
SURVEILLANCE_KEEP_THRESHOLD = 0.35   # chunk is kept only if any detection >= this
YOLO_CONF_DEFAULT = 0.35
SUPERVISOR_UNCERTAIN_THRESHOLD = 0.60
SUPERVISOR_PSEUDO_LABEL_CONF = 0.90


# -----------------------------------------------------------------------------
# SURVEILLANCE RECORDING
# -----------------------------------------------------------------------------
CHUNK_DURATION_SEC = 300             # 5 minutes per chunk
ANALYZED_RETENTION_DAYS = 7          # delete 7 days after analysis
DELETION_WARNING_SECONDS = 3600      # warn 1 hour before deletion
SWEEPER_INTERVAL_SEC = 900           # sweeper runs every 15 minutes
RECORD_AUDIO = False                 # explicitly no audio


# -----------------------------------------------------------------------------
# TOMATO VIDEO ANALYSIS SAMPLING (adaptive)
# -----------------------------------------------------------------------------
SAMPLING_SHORT_MAX_SEC = 60          # < 1 min  -> every frame
SAMPLING_MED_MAX_SEC = 300           # 1-5 min  -> every 2 s
SAMPLING_LONG_MAX_SEC = 3600         # 5-60 min -> every 5 s
SAMPLING_MED_EVERY_N_SEC = 2
SAMPLING_LONG_EVERY_N_SEC = 5
SAMPLING_VERY_LONG_EVERY_N_SEC = 10
SAMPLING_MAX_FRAMES = 2000           # hard cap to protect runtime


# -----------------------------------------------------------------------------
# CAMERA / SURVEILLANCE MODES
# -----------------------------------------------------------------------------
CAMERA_MODE_DEFAULT = "auto"         # "day" | "night" | "auto"
CHROMA_THRESHOLD = 12.0              # std of chroma below this => treat as IR/gray


# -----------------------------------------------------------------------------
# IRRIGATION (mirrors irrigation/config.py, kept here for project-wide view)
# -----------------------------------------------------------------------------
IRRIGATION_DB_FILE = DB_FILE
IRRIGATION_MODELS_FILE = os.path.join(PROJECT_ROOT, "irrigation_model.pkl")
IRRIGATION_SCALER_FILE = os.path.join(PROJECT_ROOT, "scaler.pkl")
IRRIGATION_NN_FILE = os.path.join(PROJECT_ROOT, "nn_model.h5")
IRRIGATION_RETRAIN_INTERVAL = 100


# -----------------------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------------------
VERBOSE = True


def describe() -> str:
    """Small helper used in startup logs."""
    return (
        f"PROJECT_ROOT={PROJECT_ROOT}\n"
        f"DB_FILE={DB_FILE}\n"
        f"HOST={HOST} PORT={PORT}\n"
        f"MODELS_DIR={MODELS_DIR}\n"
        f"DATASETS_DIR={DATASETS_DIR}\n"
    )


if __name__ == "__main__":
    print(describe())
