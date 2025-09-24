# Grid Alignment Fix Summary

## Problem
The grids were appearing outside the ArUco markers and floating in the air instead of being properly aligned to the ground within the marker boundaries.

## Root Causes Identified
1. **Coordinate System Mismatch**: The homography mapping and visualization code were using inconsistent coordinate systems
2. **Incorrect Grid Boundary Mapping**: The grid was being drawn across the entire coordinate space instead of being constrained to the area within the ArUco markers
3. **Inverse Homography Usage**: The visualization code was using the inverse homography incorrectly

## Changes Made

### 1. Fixed `visualize.py`
- **`project_grid_to_image()`**: Added clear comments about coordinate system mapping
- **`draw_grid()`**: Fixed grid line drawing to properly constrain within marker boundaries
- **`draw_lava_tiles()`**: Updated to use polygon-based drawing for better accuracy within grid cells

### 2. Fixed `calibrate.py`
- **`compute_homography()`**: Corrected the coordinate mapping to use proper (x=col, y=row) format
- **Preview grid drawing**: Updated to match the corrected coordinate system

### 3. Updated `mapping.py`
- **`pixel_to_grid_float()`**: Added clearer comments about coordinate system mapping

### 4. Created `test_grid_alignment.py`
- Test script to verify grid alignment within ArUco marker boundaries
- Shows grid overlay with test lava tiles to verify proper cell alignment

## How to Test

1. **First, recalibrate the system**:
   ```bash
   python calibrate.py --save
   ```
   - Place your 4 ArUco markers in the corners
   - Press 'c' when all markers are visible
   - Press 'q' to quit and save

2. **Test the grid alignment**:
   ```bash
   python test_grid_alignment.py
   ```
   - This will show the grid overlay in real-time
   - Verify that the green grid lines are within the marker boundaries
   - Red areas show test lava tiles in corner cells
   - Press 's' to save a test image
   - Press 'q' to quit

3. **Run the main server**:
   ```bash
   python server.py
   ```
   - The grid should now be properly aligned within the marker boundaries
   - Lava tiles should appear correctly within grid cells
   - Player detection should work within the constrained grid area

## Expected Results
- ✅ Grid lines appear only within the ArUco marker boundaries
- ✅ Grid is properly aligned to the ground (not floating)
- ✅ Lava tiles are constrained to grid cells
- ✅ Player foot detection works within the grid area
- ✅ Collision detection works correctly for lava tiles

## Technical Details
The key fix was ensuring that:
1. The homography maps image coordinates to a grid coordinate system where (0,0) to (cols,rows) represents the area within the markers
2. The visualization code correctly uses the inverse homography to project grid coordinates back to image space
3. All coordinate transformations are consistent throughout the pipeline

The grid is now properly constrained to the area defined by the four ArUco markers, making it suitable for the "Floor is Lava" game mechanics.
