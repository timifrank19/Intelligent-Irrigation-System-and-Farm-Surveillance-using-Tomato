# Intelligent Tomato Farm — Run Instructions

## 0. Prerequisites
- Python 3.10 or newer
- (Optional, for GPU training) CUDA 11.8+ and a compatible GPU
- Windows / Linux / macOS

## 1. Install dependencies
From the project root:

    pip install -r requirements.txt

If you have a GPU and want faster training:

    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

## 2. Download datasets (Roboflow)
Unzip each Roboflow export into the folder shown below.

    datasets/
      tomato_leaf/     <- Tomato-Leaf-Disease-60 (v60)
      tomato_fruit/    <- tomato-fruit-disease-detection-4
      human/day/       <- person-detection-in-daylight
      human/night/     <- people-detection-thermal (small version)
      animal/day/      <- farm_animals/  +  animal_detection/
      animal/night/    <- animal_detection_flir_extra

Note: for `animal/day/` unzip the two Roboflow exports into two subfolders:

    datasets/animal/day/farm_animals/
    datasets/animal/day/animal_detection/

## 3. Prepare datasets
Run each once, after the matching dataset is in place.

    python prepare_leaf_dataset.py
    python prepare_fruit_dataset.py
    python prepare_human_dataset_day.py
    python prepare_human_dataset_night.py
    python prepare_animal_dataset_day.py
    python prepare_animal_dataset_night.py

Each script rewrites `data.yaml` with absolute paths and prints class counts.

## 4. Train the YOLOv8 detectors
Run in any order. Long jobs go first.

    python train_tomato_leaf.py
    python train_tomato_fruit.py
    python train_human_day.py
    python train_human_night.py
    python train_animal_day.py
    python train_animal_night.py

Outputs:
    models/tomato_leaf/tomato_leaf.pt
    models/tomato_fruit/tomato_fruit.pt
    models/human_animal/human_day.pt
    models/human_animal/human_night.pt
    models/human_animal/animal_day.pt
    models/human_animal/animal_night.pt

## 5. Train the supervisor (optional, later)
The supervisor trains on confirmed rows in `supervisor_training_pool`.
It cannot train until you have run at least a few analyses and confirmed
them (Yes/No) in the Disease Results tab.

    python train_supervisor.py

Output:
    models/supervisor/supervisor.pt
    models/supervisor/label_map.json

If no supervisor model exists, the system runs in transparent
rule-based fallback mode (clearly labelled in the UI).

## 6. Run the C++ simulator (optional)
Keeps the irrigation dashboard alive with fresh sensor data.

Windows (MinGW or MSVC):

    g++ S_hardware.cpp -o S_hardware.exe -lwinhttp
    ./S_hardware.exe

## 7. Start the backend
From the project root:

    python irrigation_backend.py

The server binds to `0.0.0.0:8000`.

## 8. Open the frontend
Same machine:

    http://localhost:8000

Any device on the same network:

    http://<your-PC-IP>:8000

## 9. Using the app
- **Home / Dashboard / Analytics / Settings** — irrigation (no password).
- **Live Surveillance** — admin password required. Opens the browser
  camera. Records in 5-minute chunks. Chunks with no detections are
  discarded. Chunks with detections are kept and shown in "Stored
  Recordings".
- **Upload** — admin password required.
    - Image upload → instant result in the Disease Results tab.
    - Video upload → async job. Progress shows at the bottom. Result
      lands in the Disease Results tab when ready (5–10 min).
    - Analyze Stored Recording → sends a surveillance chunk to the
      tomato pipeline.
- **Disease Results** — final decision, evidence cards, recommendation,
  and Yes/No confirmation (admin feedback loop).

## 10. Admin password
The admin password is defined in `config.py`:

    ADMIN_PASSWORD = "IrrigationAdmin2024!"

It is stored in the browser's `localStorage` after first entry.
Click "Logout" in the navbar to clear it.

## 11. Retention rules
- A 5-minute chunk is discarded immediately if it has no detections ≥ 0.35.
- A kept chunk is deleted 7 days after it is analyzed.
- The user receives a WebSocket notification 1 hour before deletion,
  with a "Download Bundle" button on the Stored Recordings list.
- The bundle contains the video, event log, tomato result, and manifest.

## 12. Directory checklist (final)
    Intelligent_Tomato_Farm/
      config.py  requirements.txt  data_handler.py
      irrigation_backend.py  S_hardware.cpp
      irrigation/            (package)
      detection_memory/      (package)
      surveillance/          (package)
      tomato/                (package)
      hsv_analyzer.py  kmeans_analyzer.py  edge_analyzer.py
      supervisor.py  recommendation.py  api_handler.py
      human_animal_detector.py  surveillance_manager.py  tomato_detector.py
      prepare_*.py  train_*.py
      frontend/              (index.html + css/ + js/)
      datasets/  models/  results/  runs/

## 13. Troubleshooting
- **"model not found"** — the relevant `train_*.py` has not produced
  the `.pt` file yet. Run it after the dataset is prepared.
- **Camera won't open on another device** — browsers require `https://`
  or `localhost`. On the LAN, either use a self-signed cert or open the
  app from `http://localhost:8000` on the same machine.
- **IR rejected for tomato** — expected. The tomato pipeline requires RGB.
- **Empty recordings** — expected. Chunks with no detections are deleted
  immediately by design.
