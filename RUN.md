# Floor is Lava - Run Guide

This guide walks you through setup, calibration, and running the system, plus Unity integration.

## 1) Install Dependencies
Ensure Python 3.9–3.11. Then:
```
pip install -r requirements.txt
```

If you encounter issues with ArUco, ensure `opencv-contrib-python` is installed (included in requirements).

## 2) Generate ArUco Markers
Generate and print 4 ArUco markers with IDs 0–3:
```
python generate_markers.py --out markers/
```
- IDs mapping: 0 = top-left (TL), 1 = top-right (TR), 2 = bottom-right (BR), 3 = bottom-left (BL)
- Print at ~3–5 inches square each, high-contrast, and tape flat on the floor.
- Place the markers at the exact corners of your 8×8 ft square play area. The top edge is TL→TR, then down to BR, then to BL.

## 3) Calibrate the Room
Run calibration to estimate a homography from camera pixels → floor top-down coordinates (in grid units 0..8 for both axes), and preview the grid overlay.
```
python calibrate.py --save
```
Controls:
- Press `c` to capture when all 4 markers are clearly visible
- Press `q` to quit

Outputs:
- `homography.npy` — 3×3 homography matrix
- `grid_config.json` — grid config (rows, cols, size_feet, marker IDs)

Tip: Re-run calibration if you move the camera or the markers.

## 4) Run the Server
Start the main loop which reads the webcam, runs detection + tracking, maps to grid cells, applies lava logic, and serves WebSocket messages:
```
python server.py
```
Default configuration is read from `config.yaml`. You can edit camera index, resolution, smoothing K, WebSocket port, etc.

Controls:
- Press `q` in the video window to exit.

## 5) Debug with Demo Client
Open another terminal and run:
```
python demo_client.py
```
This connects to the server and prints incoming `detection_frame` and `event_on_lava` messages.

## 6) Unity Integration
- Add `unity/UnityWebSocketReceiver.cs` to a GameObject in your scene.
- Ensure it points to the correct WebSocket URL (default `ws://localhost:8765`).
- On connection, it will log received JSON messages. Use this stub to integrate game logic.

## 7) Sending Lava Tiles from Unity
Send messages like:
```
{
  "type": "tile_update",
  "lava_tiles": [[2,3],[4,6]]
}
```
The server will update the lava tile set. If demo mode is enabled in `config.yaml`, it will generate random tiles when no updates are received.

## 8) Notes for Performance
- Target resolution 640×480 for 10–20 FPS.
- Ensure good lighting and full visibility of feet.
- Keep the camera stable after calibration.

## Troubleshooting
- If no ArUco detection: check lighting and print quality; ensure `cv2.aruco` exists.
- If MediaPipe errors: verify CPU-only install and correct Python version.
- If WebSocket connection fails: ensure the server is running and firewall allows localhost port. 