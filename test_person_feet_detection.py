#!/usr/bin/env python3
"""
Test script with person detection first, then feet detection.
This is the reliable approach that detects persons first, then their feet.
"""

import cv2
import numpy as np
import yaml
import time
from robust_mapping import RobustPixelToGridMapper
import robust_visualize
from pose_tracker import PoseTracker
from tracker import MultiPersonTracker
from smoothing import LavaSmoother

def main():
    # Load configuration
    with open('config.yaml', 'r') as f:
        cfg = yaml.safe_load(f)
    
    # Initialize robust mapper
    mapper = RobustPixelToGridMapper()
    
    if not mapper.is_ready():
        print("ERROR: No homography found. Run robust_calibrate.py --save first.")
        return
    
    # Get grid dimensions
    rows = cfg.get('grid', {}).get('rows', 8)
    cols = cfg.get('grid', {}).get('cols', 8)
    
    print("=== FLOOR IS LAVA - PERSON + FEET DETECTION TEST ===")
    print(f"Grid dimensions: {rows}x{cols}")
    print("This test includes:")
    print("  - Person detection first, then feet detection")
    print("  - Grid alignment within ArUco markers")
    print("  - Lava collision detection")
    print("  - Press SPACE to restart after collision")
    print("\nIMPORTANT: Position camera to see your FEET, not your face!")
    print("Press 'q' to quit, 's' to save, 'l' to toggle lava tiles, SPACE to restart")
    
    # Initialize camera
    cam_idx = cfg.get('camera_index', 0)
    res = cfg.get('resolution', {'width': 640, 'height': 480})
    cap = cv2.VideoCapture(cam_idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, res['width'])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, res['height'])
    
    # Initialize person detection
    pose_tracker = PoseTracker()
    person_tracker = MultiPersonTracker()
    lava_smoother = LavaSmoother(k_consecutive=3, m_clear=2)
    
    # Game state
    lava_tiles = {(0, 0), (1, 1)}  # Start with corner cells as lava
    game_active = True
    collision_detected = False
    collision_message = ""
    frame_count = 0
    last_collision_time = 0
    collision_cooldown = 2.0  # 2 seconds between collision messages
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        frame_count += 1
        
        # Detect persons first, then their feet
        players_det = pose_tracker.process(frame)
        tracks = person_tracker.update(players_det)
        
        # Process each person and their feet
        current_time = time.time()
        
        for pid, track in tracks.items():
            det = track['last_det']
            left_px = det['left']['pixel']
            right_px = det['right']['pixel']
            left_conf = float(det['left'].get('confidence', 0.0))
            right_conf = float(det['right'].get('confidence', 0.0))

            # Convert to grid coordinates
            l_row, l_col, l_oob = mapper.pixel_to_grid_cell(left_px[0], left_px[1])
            r_row, r_col, r_oob = mapper.pixel_to_grid_cell(right_px[0], right_px[1])

            # Check for lava collisions
            for foot_name, (row, col, oob) in [('left', (l_row, l_col, l_oob)), ('right', (r_row, r_col, r_oob))]:
                if not oob and 0 <= row < rows and 0 <= col < cols and game_active:
                    is_lava = (row, col) in lava_tiles
                    triggered = lava_smoother.observe(pid, foot_name, row, col, is_lava)
                    
                    if triggered and is_lava:
                        collision_detected = True
                        collision_message = f"🔥 PERSON {pid} STEPPED INTO LAVA! Grid: ({row}, {col})"
                        if current_time - last_collision_time > collision_cooldown:
                            print(collision_message)
                            last_collision_time = current_time
        
        # Create visualization
        vis_frame = frame.copy()
        
        # Draw grid and lava tiles
        vis_frame = robust_visualize.draw_constrained_grid(vis_frame, mapper, color=(0, 255, 0), thickness=3)
        vis_frame = robust_visualize.draw_constrained_lava_tiles(vis_frame, lava_tiles, mapper, alpha=0.5)
        vis_frame = robust_visualize.draw_marker_boundaries(vis_frame, mapper, color=(255, 0, 0), thickness=2)
        
        # Draw persons and their feet
        players_for_vis = []
        for pid, track in tracks.items():
            det = track['last_det']
            left_px = det['left']['pixel']
            right_px = det['right']['pixel']
            left_conf = float(det['left'].get('confidence', 0.0))
            right_conf = float(det['right'].get('confidence', 0.0))
            
            l_row, l_col, l_oob = mapper.pixel_to_grid_cell(left_px[0], left_px[1])
            r_row, r_col, r_oob = mapper.pixel_to_grid_cell(right_px[0], right_px[1])
            
            players_for_vis.append({
                'player_id': pid,
                'left': {'pixel': [int(left_px[0]), int(left_px[1])], 'grid': [int(l_row), int(l_col)], 'confidence': left_conf, 'oob': bool(l_oob)},
                'right': {'pixel': [int(right_px[0]), int(right_px[1])], 'grid': [int(r_row), int(r_col)], 'confidence': right_conf, 'oob': bool(r_oob)},
                'centroid': [float(track['centroid'][0]), float(track['centroid'][1])]
            })
        
        vis_frame = robust_visualize.draw_players(vis_frame, players_for_vis)
        
        # Add game status
        status_text = f"Frame: {frame_count} | Persons: {len(tracks)}"
        if not game_active:
            status_text += " | GAME PAUSED"
        
        cv2.putText(vis_frame, status_text, (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add collision message
        if collision_detected and game_active:
            cv2.putText(vis_frame, collision_message, (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.putText(vis_frame, "Press SPACE to restart game", (10, 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Add instructions
        if game_active:
            cv2.putText(vis_frame, "Red areas = LAVA! Step carefully!", (10, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            cv2.putText(vis_frame, "Press SPACE to restart", (10, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        cv2.putText(vis_frame, "Press 'l' to change lava, 'q' to quit", (10, 140), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        cv2.imshow('Floor is Lava - Person + Feet Detection', vis_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f"person_feet_test_{frame_count}.jpg"
            cv2.imwrite(filename, vis_frame)
            print(f"Saved test image: {filename}")
        elif key == ord(' '):  # Space key to restart
            if collision_detected:
                game_active = True
                collision_detected = False
                collision_message = ""
                print("Game restarted!")
        elif key == ord('l'):
            # Toggle lava tiles
            if lava_tiles == {(0, 0), (1, 1)}:
                lava_tiles = {(0, 1), (1, 0)}  # Switch to other corners
                print("Lava tiles changed to: (0,1) and (1,0)")
            else:
                lava_tiles = {(0, 0), (1, 1)}  # Back to original
                print("Lava tiles changed to: (0,0) and (1,1)")
    
    cap.release()
    cv2.destroyAllWindows()
    print("Test completed.")

if __name__ == '__main__':
    main()

