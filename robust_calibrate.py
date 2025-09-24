#!/usr/bin/env python3
"""
Robust calibration that ensures proper ArUco marker detection and homography computation.
This approach focuses on getting accurate marker corners and computing a reliable homography.
"""

import argparse
import json
import time
from typing import Dict, Tuple, Optional
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

def detect_markers_robust(frame, dictionary_name: str, min_markers=4):
    """Robust marker detection with quality checks."""
    aruco = cv2.aruco
    dictionary = aruco.getPredefinedDictionary(get_aruco_dict(dictionary_name))
    parameters = aruco.DetectorParameters()
    
    # Improve detection parameters
    parameters.adaptiveThreshWinSizeMin = 3
    parameters.adaptiveThreshWinSizeMax = 23
    parameters.adaptiveThreshWinSizeStep = 10
    parameters.adaptiveThreshConstant = 7
    parameters.minMarkerPerimeterRate = 0.03
    parameters.maxMarkerPerimeterRate = 4.0
    parameters.polygonalApproxAccuracyRate = 0.03
    parameters.minCornerDistanceRate = 0.05
    parameters.minDistanceToBorder = 3
    parameters.minMarkerDistanceRate = 0.05
    parameters.cornerRefinementMethod = aruco.CORNER_REFINE_SUBPIX
    parameters.cornerRefinementWinSize = 5
    parameters.cornerRefinementMaxIterations = 30
    parameters.cornerRefinementMinAccuracy = 0.1
    parameters.markerBorderBits = 1
    parameters.perspectiveRemovePixelPerCell = 4
    parameters.perspectiveRemoveIgnoredMarginPerCell = 0.13
    parameters.maxErroneousBitsInBorderRate = 0.35
    parameters.minOtsuStdDev = 5.0
    parameters.errorCorrectionRate = 0.6
    
    detector = aruco.ArucoDetector(dictionary, parameters)
    corners, ids, _ = detector.detectMarkers(frame)
    
    if ids is None or len(ids) < min_markers:
        return corners, ids, False
    
    return corners, ids, True

def order_markers_by_ids(corners, ids, marker_ids_map: Dict[str, int]) -> Tuple[np.ndarray, bool]:
    """Order markers by their IDs and return corner points."""
    if ids is None:
        return np.zeros((4, 2)), False
    
    id_to_corners = {}
    for c, i in zip(corners, ids.flatten().tolist()):
        # Get the four corners of the marker
        marker_corners = c.reshape(-1, 2)
        id_to_corners[i] = marker_corners
    
    required = [marker_ids_map['TL'], marker_ids_map['TR'], marker_ids_map['BR'], marker_ids_map['BL']]
    if not all(mid in id_to_corners for mid in required):
        return np.zeros((4, 2)), False
    
    # Use the top-left corner of each marker as the reference point
    ordered = np.array([
        id_to_corners[marker_ids_map['TL']][0],  # Top-left corner of TL marker
        id_to_corners[marker_ids_map['TR']][1],  # Top-right corner of TR marker
        id_to_corners[marker_ids_map['BR']][2],  # Bottom-right corner of BR marker
        id_to_corners[marker_ids_map['BL']][3],  # Bottom-left corner of BL marker
    ], dtype=np.float32)
    
    return ordered, True

def compute_robust_homography(image_pts: np.ndarray, rows: int, cols: int) -> Tuple[np.ndarray, float]:
    """Compute homography with quality assessment."""
    # Define grid points: TL->(0,0), TR->(cols,0), BR->(cols,rows), BL->(0,rows)
    grid_pts = np.array([
        [0.0, 0.0],           # TL
        [float(cols), 0.0],   # TR
        [float(cols), float(rows)],  # BR
        [0.0, float(rows)]    # BL
    ], dtype=np.float32)
    
    # Compute homography
    H, mask = cv2.findHomography(image_pts, grid_pts, method=cv2.RANSAC, 
                                 ransacReprojThreshold=5.0)
    
    if H is None:
        return None, 0.0
    
    # Calculate quality metrics
    inliers = np.sum(mask) if mask is not None else 4
    quality = inliers / 4.0  # Should be 1.0 for perfect alignment
    
    # Additional quality checks
    det = np.linalg.det(H)
    cond = np.linalg.cond(H)
    
    # Quality is reduced if determinant is negative or condition number is high
    if det < 0:
        quality *= 0.5
    if cond > 1000:
        quality *= 0.8
    
    return H, quality

def validate_homography(H: np.ndarray, image_pts: np.ndarray, rows: int, cols: int) -> bool:
    """Validate that the homography produces reasonable results."""
    if H is None:
        return False
    
    # Test projection of grid corners back to image
    grid_corners = np.array([
        [0.0, 0.0],
        [float(cols), 0.0],
        [float(cols), float(rows)],
        [0.0, float(rows)]
    ], dtype=np.float32)
    
    H_inv = np.linalg.inv(H)
    projected_corners = []
    
    for corner in grid_corners:
        pt = np.array([corner[0], corner[1], 1.0])
        img_pt = H_inv.dot(pt)
        img_pt /= img_pt[2]
        projected_corners.append(img_pt[:2])
    
    projected_corners = np.array(projected_corners)
    
    # Check if projected corners are reasonable
    # They should be close to the original image points
    distances = np.linalg.norm(projected_corners - image_pts, axis=1)
    max_distance = np.max(distances)
    
    # If the maximum distance is too large, the homography is poor
    return max_distance < 50.0  # Adjust threshold as needed

def main():
    parser = argparse.ArgumentParser(description='Robust calibration using 4 ArUco markers')
    parser.add_argument('--save', action='store_true', help='Save homography and grid config')
    parser.add_argument('--quality-threshold', type=float, default=0.8, 
                       help='Minimum quality threshold for homography (0.0-1.0)')
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

    print("=== ROBUST ARUCO CALIBRATION ===")
    print("Press 'c' to capture when all 4 markers are visible and stable.")
    print("Press 'q' to quit.")
    print(f"Quality threshold: {args.quality_threshold}")

    H = None
    best_quality = 0.0
    best_image_pts = None

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # Detect markers
        corners, ids, detection_ok = detect_markers_robust(frame, aruco_name)
        
        # Draw detected markers
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            
            # Try to order markers
            ordered, order_ok = order_markers_by_ids(corners, ids, marker_ids_map)
            
            if order_ok:
                # Compute homography
                H_test, quality = compute_robust_homography(ordered, rows, cols)
                
                if H_test is not None and quality > best_quality:
                    # Validate homography
                    if validate_homography(H_test, ordered, rows, cols):
                        H = H_test
                        best_quality = quality
                        best_image_pts = ordered.copy()
                        print(f"New best homography quality: {quality:.3f}")
                
                # Draw current marker corners
                for i, pt in enumerate(ordered):
                    cv2.circle(frame, (int(pt[0]), int(pt[1])), 8, (0, 255, 0), -1)
                    cv2.putText(frame, f"C{i}", (int(pt[0]) + 10, int(pt[1]) - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw current best homography preview
        if H is not None:
            H_inv = np.linalg.inv(H)
            preview = frame.copy()
            
            # Draw grid lines
            for r in range(rows + 1):
                p1 = H_inv.dot(np.array([0.0, r, 1.0])); p1 /= p1[2]
                p2 = H_inv.dot(np.array([float(cols), r, 1.0])); p2 /= p2[2]
                cv2.line(preview, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 255, 0), 2)
            
            for c in range(cols + 1):
                p1 = H_inv.dot(np.array([c, 0.0, 1.0])); p1 /= p1[2]
                p2 = H_inv.dot(np.array([c, float(rows), 1.0])); p2 /= p2[2]
                cv2.line(preview, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 255, 0), 2)
            
            frame = preview

        # Add status information
        status_text = f"Markers: {len(ids) if ids is not None else 0}/4"
        if H is not None:
            status_text += f" | Quality: {best_quality:.3f}"
            if best_quality >= args.quality_threshold:
                status_text += " | READY TO SAVE"
            else:
                status_text += f" | Need {args.quality_threshold:.3f}"
        
        cv2.putText(frame, status_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Press 'c' to capture, 'q' to quit", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        cv2.imshow('Robust Calibration', frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('c'):
            if H is not None and best_quality >= args.quality_threshold:
                print(f"Captured homography with quality: {best_quality:.3f}")
                # Show preview
                cv2.imshow('Calibration Preview', frame)
                cv2.waitKey(1000)
            else:
                print(f"Homography quality {best_quality:.3f} below threshold {args.quality_threshold}")

    cap.release()
    cv2.destroyAllWindows()

    if args.save and H is not None and best_quality >= args.quality_threshold:
        np.save('homography.npy', H)
        with open('grid_config.json', 'w') as f:
            json.dump({
                'rows': rows, 
                'cols': cols, 
                'marker_ids': marker_ids_map,
                'quality': best_quality
            }, f, indent=2)
        print(f'Saved homography.npy and grid_config.json (quality: {best_quality:.3f})')
    elif H is None:
        print('No valid homography computed.')
    else:
        print(f'Homography quality {best_quality:.3f} below threshold {args.quality_threshold}')

if __name__ == '__main__':
    main()
