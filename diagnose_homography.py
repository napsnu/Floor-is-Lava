#!/usr/bin/env python3
"""
Diagnostic tool to analyze homography quality and grid projection issues.
This will help identify why grids are still appearing outside marker boundaries.
"""

import cv2
import numpy as np
import yaml
from mapping import PixelToGridMapper

def analyze_homography_quality(H):
    """Analyze the quality of the homography matrix."""
    print("=== HOMOGRAPHY ANALYSIS ===")
    print(f"Homography matrix:\n{H}")
    
    # Check determinant
    det = np.linalg.det(H)
    print(f"Determinant: {det:.6f}")
    
    # Check condition number
    cond = np.linalg.cond(H)
    print(f"Condition number: {cond:.2f}")
    
    # Check if it's well-conditioned
    if cond > 1000:
        print("⚠️  WARNING: Poorly conditioned matrix (condition number > 1000)")
    else:
        print("✅ Matrix is well-conditioned")
    
    # Check determinant sign
    if det < 0:
        print("⚠️  WARNING: Negative determinant - possible reflection")
    else:
        print("✅ Positive determinant")
    
    return det, cond

def test_marker_corners_projection(H, rows, cols):
    """Test how marker corners project to grid space."""
    print("\n=== MARKER CORNER PROJECTION TEST ===")
    
    # Define the four corners of the grid in grid space
    grid_corners = np.array([
        [0, 0],           # TL
        [cols, 0],        # TR  
        [cols, rows],     # BR
        [0, rows]         # BL
    ], dtype=np.float32)
    
    print("Grid corners (col, row):")
    for i, corner in enumerate(grid_corners):
        print(f"  Corner {i}: {corner}")
    
    # Project back to image space using inverse homography
    H_inv = np.linalg.inv(H)
    image_corners = []
    
    for corner in grid_corners:
        pt = np.array([corner[0], corner[1], 1.0])
        img_pt = H_inv.dot(pt)
        img_pt /= img_pt[2]
        image_corners.append((int(img_pt[0]), int(img_pt[1])))
        print(f"  Projects to image: {image_corners[-1]}")
    
    return image_corners

def test_grid_boundaries(H, rows, cols):
    """Test grid boundary projection."""
    print("\n=== GRID BOUNDARY TEST ===")
    
    # Test points along the grid boundaries
    test_points = []
    
    # Top and bottom edges
    for c in range(cols + 1):
        test_points.append((0, c))      # Top edge
        test_points.append((rows, c))   # Bottom edge
    
    # Left and right edges  
    for r in range(rows + 1):
        test_points.append((r, 0))      # Left edge
        test_points.append((r, cols))   # Right edge
    
    H_inv = np.linalg.inv(H)
    projected_points = []
    
    print(f"Testing {len(test_points)} boundary points...")
    for r, c in test_points:
        pt = np.array([c, r, 1.0])
        img_pt = H_inv.dot(pt)
        img_pt /= img_pt[2]
        projected_points.append((int(img_pt[0]), int(img_pt[1])))
    
    # Find bounding box of projected points
    x_coords = [p[0] for p in projected_points]
    y_coords = [p[1] for p in projected_points]
    
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    
    print(f"Projected grid bounds: x=[{min_x}, {max_x}], y=[{min_y}, {max_y}]")
    print(f"Grid span: {max_x - min_x} x {max_y - min_y} pixels")
    
    return projected_points, (min_x, min_y, max_x, max_y)

def visualize_diagnosis(frame, H, rows, cols):
    """Create a diagnostic visualization."""
    if H is None:
        return frame
    
    H_inv = np.linalg.inv(H)
    vis = frame.copy()
    
    # Draw grid lines
    for r in range(rows + 1):
        p1 = H_inv.dot(np.array([0.0, r, 1.0])); p1 /= p1[2]
        p2 = H_inv.dot(np.array([float(cols), r, 1.0])); p2 /= p2[2]
        cv2.line(vis, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 255, 0), 2)
    
    for c in range(cols + 1):
        p1 = H_inv.dot(np.array([c, 0.0, 1.0])); p1 /= p1[2]
        p2 = H_inv.dot(np.array([c, float(rows), 1.0])); p2 /= p2[2]
        cv2.line(vis, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 255, 0), 2)
    
    # Draw corner markers
    grid_corners = [(0, 0), (cols, 0), (cols, rows), (0, rows)]
    for i, (c, r) in enumerate(grid_corners):
        pt = np.array([c, r, 1.0])
        img_pt = H_inv.dot(pt)
        img_pt /= img_pt[2]
        cv2.circle(vis, (int(img_pt[0]), int(img_pt[1])), 8, (0, 0, 255), -1)
        cv2.putText(vis, f"C{i}", (int(img_pt[0]) + 10, int(img_pt[1]) - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    return vis

def main():
    # Load configuration
    with open('config.yaml', 'r') as f:
        cfg = yaml.safe_load(f)
    
    # Initialize mapper
    mapper = PixelToGridMapper()
    
    if not mapper.is_ready():
        print("ERROR: No homography found. Run calibrate.py --save first.")
        return
    
    rows = cfg.get('grid', {}).get('rows', 8)
    cols = cfg.get('grid', {}).get('cols', 8)
    
    print(f"Grid dimensions: {rows}x{cols}")
    print("=" * 50)
    
    # Analyze homography quality
    det, cond = analyze_homography_quality(mapper.H)
    
    # Test marker corner projection
    image_corners = test_marker_corners_projection(mapper.H, rows, cols)
    
    # Test grid boundaries
    projected_points, bounds = test_grid_boundaries(mapper.H, rows, cols)
    
    # Visualize with camera
    cam_idx = cfg.get('camera_index', 0)
    res = cfg.get('resolution', {'width': 640, 'height': 480})
    cap = cv2.VideoCapture(cam_idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, res['width'])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, res['height'])
    
    print("\n=== LIVE DIAGNOSTIC VIEW ===")
    print("Press 'q' to quit, 's' to save diagnostic image")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        vis = visualize_diagnosis(frame, mapper.H, rows, cols)
        
        # Add diagnostic info
        cv2.putText(vis, f"Det: {det:.3f}, Cond: {cond:.1f}", (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(vis, f"Grid bounds: {bounds[0]},{bounds[1]} to {bounds[2]},{bounds[3]}", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        cv2.imshow('Homography Diagnostic', vis)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = "homography_diagnostic.jpg"
            cv2.imwrite(filename, vis)
            print(f"Saved diagnostic image: {filename}")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
