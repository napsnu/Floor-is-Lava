import json
from typing import Optional, Tuple, List

import numpy as np


class PixelToGridMapper:
    def __init__(self, homography_path: str = 'homography.npy', grid_config_path: str = 'grid_config.json'):
        self.H: Optional[np.ndarray] = None
        self.rows = 8
        self.cols = 8
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

    def pixel_to_grid_float(self, x: float, y: float) -> Tuple[float, float]:
        if self.H is None:
            return -1.0, -1.0
        pt = np.array([x, y, 1.0], dtype=np.float64)
        world = self.H.dot(pt)
        world /= world[2] + 1e-9
        X, Y = world[0], world[1]
        # Homography maps to (col, row) coordinates where col=0..cols, row=0..rows
        return float(Y), float(X)  # map to [row, col]

    def pixel_to_grid_cell(self, x: int, y: int) -> Tuple[int, int, bool]:
        row_f, col_f = self.pixel_to_grid_float(x, y)
        # For 2x2 grid, clamp to valid range [0,1] for both row and col
        row = int(np.clip(np.floor(row_f), 0, self.rows - 1))
        col = int(np.clip(np.floor(col_f), 0, self.cols - 1))
        outside = row_f < 0 or col_f < 0 or row_f >= self.rows or col_f >= self.cols
        return row, col, outside

    def grid_lines(self) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        # Returns grid lines in grid space for visualization
        lines = []
        for r in range(self.rows + 1):
            lines.append(((r, 0), (r, self.cols)))
        for c in range(self.cols + 1):
            lines.append(((0, c), (self.rows, c)))
        return lines 