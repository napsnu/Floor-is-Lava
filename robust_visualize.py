#!/usr/bin/env python3
"""
Robust visualization module that ensures grids are properly constrained within ArUco markers.
"""

import cv2
import numpy as np
from typing import Dict, List, Set, Tuple, Optional
from robust_mapping import RobustPixelToGridMapper

def draw_constrained_grid(frame, mapper: RobustPixelToGridMapper, color=(0, 255, 0), thickness=3):
    """Draw grid lines that are strictly constrained within marker boundaries."""
    if not mapper.is_ready():
        return frame
    
    # Get grid lines from the robust mapper
    lines = mapper.get_grid_lines_within_markers()
    
    # Draw each line
    for (p1, p2) in lines:
        pt1 = (int(p1[0]), int(p1[1]))
        pt2 = (int(p2[0]), int(p2[1]))
        cv2.line(frame, pt1, pt2, color, thickness, cv2.LINE_AA)
    
    return frame

def draw_constrained_lava_tiles(frame, lava_tiles: Set[Tuple[int, int]], mapper: RobustPixelToGridMapper, 
                               alpha: float = 0.35, color=(0, 0, 255)):
    """Draw lava tiles that are constrained within grid cells."""
    if not mapper.is_ready() or not lava_tiles:
        return frame
    
    overlay = frame.copy()
    
    for (row, col) in lava_tiles:
        # Get the four corners of the grid cell
        corners = mapper.get_grid_cell_corners(row, col)
        
        if len(corners) == 4:
            # Convert to integer points for OpenCV
            pts = np.array([(int(x), int(y)) for x, y in corners], np.int32)
            cv2.fillPoly(overlay, [pts], color)
    
    # Blend with original frame
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    return frame

def draw_marker_boundaries(frame, mapper: RobustPixelToGridMapper, color=(255, 0, 0), thickness=2):
    """Draw the ArUco marker boundaries."""
    if not mapper.is_ready():
        return frame
    
    marker_polygon = mapper.get_marker_boundary_polygon()
    if marker_polygon is not None:
        # Draw the marker boundary
        cv2.polylines(frame, [marker_polygon.astype(np.int32)], True, color, thickness)
        
        # Draw corner points
        for i, point in enumerate(marker_polygon):
            cv2.circle(frame, (int(point[0]), int(point[1])), 5, color, -1)
            cv2.putText(frame, f"M{i}", (int(point[0]) + 5, int(point[1]) - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    return frame

def draw_grid_cell_numbers(frame, mapper: RobustPixelToGridMapper, color=(255, 255, 255)):
    """Draw grid cell numbers for debugging."""
    if not mapper.is_ready():
        return frame
    
    for row in range(mapper.rows):
        for col in range(mapper.cols):
            # Get cell center
            corners = mapper.get_grid_cell_corners(row, col)
            if len(corners) == 4:
                # Calculate center of the cell
                center_x = int(sum(pt[0] for pt in corners) / 4)
                center_y = int(sum(pt[1] for pt in corners) / 4)
                
                # Draw cell number
                cv2.putText(frame, f"{row},{col}", (center_x - 10, center_y + 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    return frame

def draw_players(frame, players: List[Dict]):
    """Draw player positions with grid coordinates."""
    for p in players:
        pid = p.get('player_id', -1)
        left = p.get('left', {})
        right = p.get('right', {})
        
        for foot, color in [(left, (255, 255, 0)), (right, (255, 0, 255))]:
            pix = foot.get('pixel')
            conf = foot.get('confidence', 0.0)
            if pix:
                cv2.circle(frame, (int(pix[0]), int(pix[1])), 6, color, -1)
                
                # Draw grid coordinates
                grid = foot.get('grid', [])
                if grid:
                    cv2.putText(frame, f"({grid[0]},{grid[1]})", 
                               (int(pix[0]) + 10, int(pix[1]) - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # Draw player ID near centroid
        if 'centroid' in p:
            cx, cy = map(int, p['centroid'])
        else:
            if left.get('pixel') and right.get('pixel'):
                cx = int((left['pixel'][0] + right['pixel'][0]) / 2)
                cy = int((left['pixel'][1] + right['pixel'][1]) / 2)
            else:
                continue
        
        cv2.putText(frame, f"ID {pid}", (cx + 8, cy - 8), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    return frame

def draw_fps(frame, fps: float):
    """Draw FPS counter."""
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 255, 50), 2)
    return frame

def draw_latency(frame, latency_ms: float):
    """Draw latency counter."""
    cv2.putText(frame, f"Latency: {latency_ms:.0f} ms", (10, 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 200, 255), 2)
    return frame

def create_debug_overlay(frame, mapper: RobustPixelToGridMapper, lava_tiles: Set[Tuple[int, int]]):
    """Create a comprehensive debug overlay."""
    vis = frame.copy()
    
    # Draw marker boundaries
    vis = draw_marker_boundaries(vis, mapper, color=(255, 0, 0), thickness=2)
    
    # Draw constrained grid
    vis = draw_constrained_grid(vis, mapper, color=(0, 255, 0), thickness=2)
    
    # Draw lava tiles
    vis = draw_constrained_lava_tiles(vis, lava_tiles, mapper, alpha=0.5)
    
    # Draw grid cell numbers
    vis = draw_grid_cell_numbers(vis, mapper, color=(255, 255, 255))
    
    return vis
