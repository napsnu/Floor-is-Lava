# Floor is Lava - AI/Computer Vision System

This repository provides a complete, production-ready Python system (plus Unity receiver stub) to power the "Floor is Lava" game using a laptop webcam. It tracks up to 4 players, calibrates a real-world 8×8 ft room into an 8×8 grid using ArUco markers, detects players’ feet via MediaPipe Pose, maps feet to grid cells, applies lava collision logic with smoothing, and streams events over WebSocket.

## Quick Start

1) Create and activate a virtual environment, then install dependencies:
```
pip install -r requirements.txt
```

2) Generate and print ArUco markers (IDs 0–3):
```
python generate_markers.py --out markers/
```

3) Calibrate the room with 4 markers on the floor corners (IDs TL=0, TR=1, BR=2, BL=3):
```
python calibrate.py --save
```

4) Run the server (webcam index 0 by default):
```
python server.py
```

5) Optional: Run the demo client to view messages:
```
python demo_client.py
```

6) Unity: Import `unity/UnityWebSocketReceiver.cs` and connect to the WebSocket server (default ws://localhost:8765).

See `RUN.md` for the step-by-step guide including printing and placing markers, calibration verification, and Unity setup.

## Features
- Laptop webcam (index 0)
- Calibration via 4 ArUco markers, outputs `homography.npy` and `grid_config.json`
- Multi-person foot detection with MediaPipe Pose (extract LEFT_FOOT_INDEX and RIGHT_FOOT_INDEX); pluggable to YOLOv8-Pose
- Tracking with stable `player_id` via centroid + Hungarian matching
- Pixel-to-grid mapping into 8×8 cells; out-of-bounds detection
- Lava logic with smoothing (K consecutive frames)
- WebSocket server: broadcasts detection frames and on_lava events; accepts tile updates
- Visualization: camera feed, skeleton overlay, grid, lava tiles, IDs, FPS

## Repository Layout
- `generate_markers.py` – Save 4 ArUco markers (IDs 0–3)
- `calibrate.py` – Calibrate from markers, save `homography.npy` and `grid_config.json`
- `pose_tracker.py` – MediaPipe Pose wrapper to extract left/right feet
- `tracker.py` – Multi-person tracking with Hungarian matching
- `mapping.py` – Pixel→grid mapping using homography
- `smoothing.py` – Debounce lava events
- `server.py` – WebSocket server and main runtime loop
- `visualize.py` – Rendering overlays for debugging
- `demo_client.py` – Simple client to print messages
- `unity/UnityWebSocketReceiver.cs` – Example Unity C# script (stub)
- `tests/` – Unit tests

## License
MIT — see `LICENSE`. 