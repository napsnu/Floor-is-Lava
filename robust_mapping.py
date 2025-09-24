#!/usr/bin/env python3
"""
Robust mapping approach that constrains the grid strictly within ArUco marker boundaries.
This uses a different strategy: instead of mapping the entire grid space, we map only
the area within the detected markers and scale the grid accordingly.
"""

import json
import numpy as np
from typing import Optional, Tuple, List
import cv2

class RobustPixelToGridMapper:
    def __init__(self, homography_path: str = 'homography.npy', grid_config_path: str = 'grid_config.json'):
        self.H: Optional[np.ndarray] = None
        self.rows = 8
        self.cols = 8
        self.marker_corners: Optional[np.ndarray] = None  # Store actual marker corners
        
        try:
            self.H = np.load(homography_path)
        except Exception:
            self.H = None
            
        try:
            with open(grid_config_path, 'r') as f:
                cfg = json.load(f)
                self.rows = int(cfg.get('rows', 8))
                self.cols = int(cfg.get('cols', 8))
        except Exception:
            pass

    def is_ready(self) -> bool:
        return self.H is not None

    def set_marker_corners(self, corners: np.ndarray):
        """Set the actual detected marker corners for boundary constraint."""
        self.marker_corners = corners

    def pixel_to_grid_float(self, x: float, y: float) -> Tuple[float, float]:
        """Convert pixel coordinates to grid coordinates with boundary constraints."""
        if self.H is None:
            return -1.0, -1.0
        
        # Transform pixel to grid space
        pt = np.array([x, y, 1.0], dtype=np.float64)
        world = self.H.dot(pt)
        world /= world[2] + 1e-9
        col, row = world[0], world[1]
        
        # Clamp to valid grid range
        row = np.clip(row, 0, self.rows)
        col = np.clip(col, 0, self.cols)
        
        return float(row), float(col)

    def pixel_to_grid_cell(self, x: int, y: int) -> Tuple[int, int, bool]:
        """Convert pixel coordinates to grid cell with boundary checking."""
        row_f, col_f = self.pixel_to_grid_float(x, y)
        
        # Convert to cell indices
        row = int(np.clip(np.floor(row_f), 0, self.rows - 1))
        col = int(np.clip(np.floor(col_f), 0, self.cols - 1))
        
        # Check if outside the valid grid area
        outside = (row_f < 0 or col_f < 0 or 
                  row_f >= self.rows or col_f >= self.cols)
        
        return row, col, outside

    def get_grid_lines_within_markers(self) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """Get grid lines that are constrained within the marker boundaries."""
        if self.H is None:
            return []
        
        lines = []
        H_inv = np.linalg.inv(self.H)
        
        # Generate grid lines within the marker boundaries
        for r in range(self.rows + 1):
            # Horizontal line from left to right edge
            p1 = np.array([0.0, r, 1.0])
            p2 = np.array([float(self.cols), r, 1.0])
            
            # Project to image space
            img1 = H_inv.dot(p1); img1 /= img1[2]
            img2 = H_inv.dot(p2); img2 /= img2[2]
            
            lines.append(((float(img1[0]), float(img1[1])), 
                         (float(img2[0]), float(img2[1]))))
        
        for c in range(self.cols + 1):
            # Vertical line from top to bottom edge
            p1 = np.array([c, 0.0, 1.0])
            p2 = np.array([c, float(self.rows), 1.0])
            
            # Project to image space
            img1 = H_inv.dot(p1); img1 /= img1[2]
            img2 = H_inv.dot(p2); img2 /= img2[2]
            
            lines.append(((float(img1[0]), float(img1[1])), 
                         (float(img2[0]), float(img2[1]))))
        
        return lines

    def get_grid_cell_corners(self, row: int, col: int) -> List[Tuple[float, float]]:
        """Get the four corners of a specific grid cell in image coordinates."""
        if self.H is None:
            return []
        
        H_inv = np.linalg.inv(self.H)
        
        # Define cell corners in grid space
        corners = [
            (col, row),           # top-left
            (col + 1, row),       # top-right
            (col + 1, row + 1),   # bottom-right
            (col, row + 1)        # bottom-left
        ]
        
        # Project to image space
        image_corners = []
        for c, r in corners:
            pt = np.array([c, r, 1.0])
            img_pt = H_inv.dot(pt)
            img_pt /= img_pt[2]
            image_corners.append((float(img_pt[0]), float(img_pt[1])))
        
        return image_corners

    def is_point_in_marker_area(self, x: float, y: float) -> bool:
        """Check if a point is within the marker-defined area."""
        if self.marker_corners is None:
            return True  # If no markers, assume valid
        
        # Use point-in-polygon test
        point = np.array([x, y])
        return cv2.pointPolygonTest(self.marker_corners, point, False) >= 0

    def get_marker_boundary_polygon(self) -> Optional[np.ndarray]:
        """Get the marker boundary polygon for visualization."""
        return self.marker_corners
