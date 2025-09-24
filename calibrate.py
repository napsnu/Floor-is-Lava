import argparse
import json
import time
from typing import Dict, Tuple

import cv2
import numpy as np
import yaml


def load_config(path: str = 'config.yaml') -> Dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def get_aruco_dict(dict_name: str):
    if not hasattr(cv2, 'aruco'):
        raise RuntimeError('cv2.aruco not available, install opencv-contrib-python')
    aruco = cv2.aruco
    if not hasattr(aruco, dict_name):
        raise RuntimeError(f'ArUco dictionary {dict_name} not found')
    return getattr(aruco, dict_name)


def detect_markers(frame, dictionary_name: str):
    aruco = cv2.aruco
    dictionary = aruco.getPredefinedDictionary(get_aruco_dict(dictionary_name))
    parameters = aruco.DetectorParameters()
    detector = aruco.ArucoDetector(dictionary, parameters)
    corners, ids, _ = detector.detectMarkers(frame)
    return corners, ids


def order_points_by_ids(corners, ids, marker_ids_map: Dict[str, int]) -> Tuple[np.ndarray, bool]:
    if ids is None:
        return np.zeros((4, 2)), False
    id_to_corner_center = {}
    for c, i in zip(corners, ids.flatten().tolist()):
        pts = c.reshape(-1, 2)
        center = pts.mean(axis=0)
        id_to_corner_center[i] = center
    required = [marker_ids_map['TL'], marker_ids_map['TR'], marker_ids_map['BR'], marker_ids_map['BL']]
    if not all(mid in id_to_corner_center for mid in required):
        return np.zeros((4, 2)), False
    ordered = np.array([
        id_to_corner_center[marker_ids_map['TL']],
        id_to_corner_center[marker_ids_map['TR']],
        id_to_corner_center[marker_ids_map['BR']],
        id_to_corner_center[marker_ids_map['BL']],
    ], dtype=np.float32)
    return ordered, True


def compute_homography(image_pts: np.ndarray, rows: int, cols: int) -> np.ndarray:
    # Map image points to grid coordinates: TL->(0,0), TR->(0,cols), BR->(rows,cols), BL->(rows,0)
    # For 2x2 grid: TL->(0,0), TR->(0,2), BR->(2,2), BL->(2,0)
    # Note: OpenCV expects (x, y) format, so we use (col, row)
    grid_pts = np.array([
        [0.0, 0.0],           # TL -> (col=0, row=0)
        [float(cols), 0.0],   # TR -> (col=cols, row=0)  
        [float(cols), float(rows)],  # BR -> (col=cols, row=rows)
        [0.0, float(rows)]    # BL -> (col=0, row=rows)
    ], dtype=np.float32)
    # we map image -> grid (x=col, y=row)
    H, _ = cv2.findHomography(image_pts, grid_pts, method=0)
    return H


def main():
    parser = argparse.ArgumentParser(description='Calibrate play area using 4 ArUco markers')
    parser.add_argument('--save', action='store_true', help='Save homography and grid config')
    args = parser.parse_args()

    cfg = load_config()
    cam_idx = cfg.get('camera_index', 0)
    res = cfg.get('resolution', {'width': 640, 'height': 480})
    rows = cfg.get('grid', {}).get('rows', 8)
    cols = cfg.get('grid', {}).get('cols', 8)
    marker_ids_map = cfg.get('grid', {}).get('marker_ids', {'TL': 0, 'TR': 1, 'BR': 2, 'BL': 3})
    aruco_name = cfg.get('aruco', {}).get('dict', 'DICT_4X4_50')

    cap = cv2.VideoCapture(cam_idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, res['width'])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, res['height'])

    print("Press 'c' to capture when all 4 markers are visible. Press 'q' to quit.")

    H = None

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        corners, ids = detect_markers(frame, aruco_name)
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
        cv2.imshow('Calibration', frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord('c'):
            ordered, ok = order_points_by_ids(corners, ids, marker_ids_map)
            if not ok:
                print('All required markers not detected. Ensure IDs 0:TL,1:TR,2:BR,3:BL are visible.')
                continue
            H = compute_homography(ordered, rows, cols)
            print('Homography computed.')
            # Preview grid overlay
            H_inv = np.linalg.inv(H)
            # draw grid lines
            preview = frame.copy()
            # Draw horizontal grid lines (rows)
            for r in range(rows + 1):
                p1 = H_inv.dot(np.array([0.0, r, 1.0])); p1 /= p1[2]
                p2 = H_inv.dot(np.array([float(cols), r, 1.0])); p2 /= p2[2]
                cv2.line(preview, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 255, 0), 2)
            # Draw vertical grid lines (cols)
            for c in range(cols + 1):
                p1 = H_inv.dot(np.array([c, 0.0, 1.0])); p1 /= p1[2]
                p2 = H_inv.dot(np.array([c, float(rows), 1.0])); p2 /= p2[2]
                cv2.line(preview, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 255, 0), 2)
            cv2.imshow('Calibration Preview', preview)
            cv2.waitKey(500)

    cap.release()
    cv2.destroyAllWindows()

    if args.save and H is not None:
        np.save('homography.npy', H)
        with open('grid_config.json', 'w') as f:
            json.dump({'rows': rows, 'cols': cols, 'marker_ids': marker_ids_map}, f, indent=2)
        print('Saved homography.npy and grid_config.json')


if __name__ == '__main__':
    main() 