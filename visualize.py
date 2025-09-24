from typing import Dict, List, Set, Tuple
import time

import cv2
import numpy as np


def project_grid_to_image(grid_points: List[Tuple[float, float]], H_inv: np.ndarray) -> List[Tuple[int, int]]:
    pts = []
    for (r, c) in grid_points:
        # Grid space: (row, col) where row=0..rows, col=0..cols
        # Map to homography input format: (col, row, 1) for H_inv
        pt = np.array([c, r, 1.0], dtype=np.float64)
        img = H_inv.dot(pt)
        img /= img[2] + 1e-9
        pts.append((int(img[0]), int(img[1])))
    return pts


def draw_grid(frame, rows: int, cols: int, H: np.ndarray, color=(0, 255, 0)):
    if H is None:
        return frame
    H_inv = np.linalg.inv(H)
    # draw grid lines - make them thicker for 2x2 grid
    thickness = 3
    
    # Draw horizontal grid lines (rows)
    for r in range(rows + 1):
        # Each horizontal line goes from col 0 to col cols
        p1 = project_grid_to_image([(r, 0)], H_inv)[0]
        p2 = project_grid_to_image([(r, cols)], H_inv)[0]
        cv2.line(frame, p1, p2, color, thickness, cv2.LINE_AA)
    
    # Draw vertical grid lines (cols)  
    for c in range(cols + 1):
        # Each vertical line goes from row 0 to row rows
        p1 = project_grid_to_image([(0, c)], H_inv)[0]
        p2 = project_grid_to_image([(rows, c)], H_inv)[0]
        cv2.line(frame, p1, p2, color, thickness, cv2.LINE_AA)
    
    return frame


def draw_lava_tiles(frame, lava_tiles: Set[Tuple[int, int]], H: np.ndarray, alpha: float = 0.35):
    if H is None or not lava_tiles:
        return frame
    H_inv = np.linalg.inv(H)
    overlay = frame.copy()
    for (r, c) in lava_tiles:
        # For 2x2 grid, each cell spans from (r,c) to (r+1,c+1)
        # Get the four corners of the grid cell
        p1 = project_grid_to_image([(r, c)], H_inv)[0]      # top-left
        p2 = project_grid_to_image([(r, c + 1)], H_inv)[0]  # top-right  
        p3 = project_grid_to_image([(r + 1, c + 1)], H_inv)[0]  # bottom-right
        p4 = project_grid_to_image([(r + 1, c)], H_inv)[0]  # bottom-left
        
        # Create polygon from the four corners
        pts = np.array([p1, p2, p3, p4], np.int32)
        cv2.fillPoly(overlay, [pts], (0, 0, 255))
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    return frame


def draw_players(frame, players: List[Dict]):
    for p in players:
        pid = p.get('player_id', -1)
        left = p.get('left', {})
        right = p.get('right', {})
        for foot, color in [(left, (255, 255, 0)), (right, (255, 0, 255))]:
            pix = foot.get('pixel')
            conf = foot.get('confidence', 0.0)
            if pix:
                cv2.circle(frame, (int(pix[0]), int(pix[1])), 6, color, -1)
        # draw id near centroid if available
        if 'centroid' in p:
            cx, cy = map(int, p['centroid'])
        else:
            # fallback: average feet
            if left.get('pixel') and right.get('pixel'):
                cx = int((left['pixel'][0] + right['pixel'][0]) / 2)
                cy = int((left['pixel'][1] + right['pixel'][1]) / 2)
            else:
                continue
        cv2.putText(frame, f"ID {pid}", (cx + 8, cy - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return frame


def draw_fps(frame, fps: float):
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 255, 50), 2)
    return frame 


def draw_latency(frame, latency_ms: float):
    cv2.putText(frame, f"Latency: {latency_ms:.0f} ms", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 200, 255), 2)
    return frame