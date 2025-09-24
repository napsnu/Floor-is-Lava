#!/usr/bin/env python3
"""
Robust server with person detection first, then feet detection.
Better for multiplayer scenarios where we need to track which feet belong to which person.
"""

import asyncio
import json
import logging
import random
import time
import socket
from typing import Dict, List, Set, Tuple

import cv2
import numpy as np
import websockets
import yaml

from robust_mapping import RobustPixelToGridMapper
from pose_tracker import PoseTracker
from smoothing import LavaSmoother
from tracker import MultiPersonTracker
import robust_visualize

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger('robust_lava_server')

class RobustLavaServer:
    def __init__(self, cfg: Dict):
        self.cfg = cfg
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.port = cfg.get('websocket_port', 8765)
        self.rows = cfg.get('grid', {}).get('rows', 8)
        self.cols = cfg.get('grid', {}).get('cols', 8)
        self.demo_cfg = cfg.get('demo_mode', {})
        self.demo_enabled = bool(self.demo_cfg.get('enabled', True))
        self.demo_interval = float(self.demo_cfg.get('interval_seconds', 2))
        self.demo_tiles_num = int(self.demo_cfg.get('tiles_per_interval', 6))
        self.lava_tiles: Set[Tuple[int, int]] = set()
        self.frame_id = 0
        self.last_demo_time = 0.0
        
        # Game state
        self.game_active = True
        self.collision_detected = False
        self.collision_message = ""
        self.last_collision_time = 0
        self.collision_cooldown = 2.0
        
        # UDP optional
        udp_cfg = cfg.get('udp', {})
        self.udp_enabled = bool(udp_cfg.get('enabled', False))
        self.udp_host = udp_cfg.get('host', '127.0.0.1')
        self.udp_port = int(udp_cfg.get('port', 9876))
        self.udp_sock = None
        if self.udp_enabled:
            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Video
        cam_idx = cfg.get('camera_index', 0)
        res = cfg.get('resolution', {'width': 640, 'height': 480})
        self.cap = cv2.VideoCapture(cam_idx)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, res['width'])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, res['height'])

        # Processing components
        self.pose = PoseTracker()
        self.tracker = MultiPersonTracker()
        self.mapper = RobustPixelToGridMapper()
        self.smoother = LavaSmoother(
            k_consecutive=cfg.get('smoothing', {}).get('consecutive_frames', 3),
            m_clear=cfg.get('smoothing', {}).get('clear_frames', 2),
        )

        if not self.mapper.is_ready():
            logger.warning('Homography not found. Run robust_calibrate.py --save first. Mapping will not work.')
        
        # ArUco detection for marker boundary detection
        self.aruco_dict = None
        self.aruco_params = None
        self.aruco_detector = None
        self._init_aruco_detection()

    def _init_aruco_detection(self):
        """Initialize ArUco detection for marker boundary tracking."""
        try:
            aruco_name = self.cfg.get('aruco', {}).get('dict', 'DICT_4X4_50')
            aruco = cv2.aruco
            dictionary = aruco.getPredefinedDictionary(getattr(aruco, aruco_name))
            self.aruco_params = aruco.DetectorParameters()
            self.aruco_detector = aruco.ArucoDetector(dictionary, self.aruco_params)
            logger.info("ArUco detection initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize ArUco detection: {e}")
            self.aruco_detector = None

    def _detect_marker_boundaries(self, frame):
        """Detect ArUco markers and update mapper boundaries."""
        if self.aruco_detector is None:
            return
        
        try:
            corners, ids, _ = self.aruco_detector.detectMarkers(frame)
            if ids is not None and len(ids) >= 4:
                # Get marker corners for boundary detection
                marker_ids_map = self.cfg.get('grid', {}).get('marker_ids', {'TL': 0, 'TR': 1, 'BR': 2, 'BL': 3})
                id_to_corners = {}
                
                for c, i in zip(corners, ids.flatten().tolist()):
                    marker_corners = c.reshape(-1, 2)
                    id_to_corners[i] = marker_corners
                
                required = [marker_ids_map['TL'], marker_ids_map['TR'], marker_ids_map['BR'], marker_ids_map['BL']]
                if all(mid in id_to_corners for mid in required):
                    # Create boundary polygon from marker corners
                    boundary_corners = np.array([
                        id_to_corners[marker_ids_map['TL']][0],  # TL
                        id_to_corners[marker_ids_map['TR']][1],  # TR
                        id_to_corners[marker_ids_map['BR']][2],  # BR
                        id_to_corners[marker_ids_map['BL']][3],  # BL
                    ], dtype=np.float32)
                    
                    self.mapper.set_marker_corners(boundary_corners)
        except Exception as e:
            logger.debug(f"Marker detection error: {e}")

    def _detect_person_feet(self, frame):
        """
        Detect persons first, then detect their feet.
        This approach is better for multiplayer scenarios.
        """
        # First, detect persons using pose estimation
        players_det = self.pose.process(frame)
        tracks = self.tracker.update(players_det)
        
        # Process each person and their feet
        person_feet_data = []
        
        for pid, track in tracks.items():
            det = track['last_det']
            left_px = det['left']['pixel']
            right_px = det['right']['pixel']
            left_conf = float(det['left'].get('confidence', 0.0))
            right_conf = float(det['right'].get('confidence', 0.0))

            # Convert feet positions to grid coordinates
            l_row, l_col, l_oob = self.mapper.pixel_to_grid_cell(left_px[0], left_px[1])
            r_row, r_col, r_oob = self.mapper.pixel_to_grid_cell(right_px[0], right_px[1])

            # Store person and their feet data
            person_data = {
                'person_id': pid,
                'left_foot': {
                    'pixel': [int(left_px[0]), int(left_px[1])],
                    'grid': [int(l_row), int(l_col)],
                    'confidence': left_conf,
                    'oob': bool(l_oob)
                },
                'right_foot': {
                    'pixel': [int(right_px[0]), int(right_px[1])],
                    'grid': [int(r_row), int(r_col)],
                    'confidence': right_conf,
                    'oob': bool(r_oob)
                },
                'centroid': [float(track['centroid'][0]), float(track['centroid'][1])]
            }
            
            person_feet_data.append(person_data)
        
        return person_feet_data

    def _check_lava_collisions(self, person_feet_data):
        """Check for lava collisions for each person's feet."""
        current_time = time.time()
        collision_events = []
        
        for person in person_feet_data:
            person_id = person['person_id']
            
            # Check both feet for lava collisions
            for foot_name, foot_data in [('left', person['left_foot']), ('right', person['right_foot'])]:
                grid = foot_data['grid']
                row, col = int(grid[0]), int(grid[1])
                in_bounds = 0 <= row < self.rows and 0 <= col < self.cols
                is_lava = in_bounds and (row, col) in self.lava_tiles
                
                # Use smoother to avoid false positives
                triggered = self.smoother.observe(person_id, foot_name, row, col, is_lava)
                
                if triggered and is_lava and self.game_active:
                    if current_time - self.last_collision_time > self.collision_cooldown:
                        self.collision_detected = True
                        self.collision_message = f"🔥 PERSON {person_id} STEPPED INTO LAVA! Grid: ({row}, {col})"
                        self.last_collision_time = current_time
                        
                        collision_event = {
                            'type': 'event_on_lava',
                            'timestamp': int(time.time() * 1000),
                            'person_id': person_id,
                            'foot': foot_name,
                            'grid': [row, col],
                            'consecutive_frames': self.smoother.k
                        }
                        collision_events.append(collision_event)
                        
                        logger.info(f"Person {person_id} stepped into lava at grid ({row}, {col})")
        
        return collision_events

    async def handler(self, websocket):
        self.clients.add(websocket)
        logger.info('Client connected')
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                except Exception as e:
                    logger.warning(f'Invalid JSON from client: {e}')
                    continue
                await self._handle_message(data)
        finally:
            self.clients.discard(websocket)
            logger.info('Client disconnected')

    async def _handle_message(self, data: Dict):
        if data.get('type') == 'tile_update':
            incoming = data.get('lava_tiles', [])
            new_tiles = set()
            for t in incoming:
                if isinstance(t, list) and len(t) == 2:
                    r, c = int(t[0]), int(t[1])
                    if 0 <= r < self.rows and 0 <= c < self.cols:
                        new_tiles.add((r, c))
            self.lava_tiles = new_tiles
            logger.info(f'Updated lava tiles: {sorted(list(self.lava_tiles))}')
        elif data.get('type') == 'restart_game':
            # Restart game
            self.game_active = True
            self.collision_detected = False
            self.collision_message = ""
            logger.info('Game restarted by client')
        else:
            logger.debug(f'Unknown message: {data}')

    async def broadcast(self, payload: Dict):
        if not self.clients:
            return
        msg = json.dumps(payload)
        await asyncio.gather(*[self._safe_send(c, msg) for c in list(self.clients)])
        # UDP mirror
        if self.udp_enabled and self.udp_sock is not None:
            try:
                self.udp_sock.sendto((msg + "\n").encode('utf-8'), (self.udp_host, self.udp_port))
            except Exception:
                pass

    async def _safe_send(self, client, msg: str):
        try:
            await client.send(msg)
        except Exception:
            self.clients.discard(client)

    def _maybe_demo_tiles(self):
        now = time.time()
        if not self.demo_enabled:
            return
        if self.clients and now - self.last_demo_time > self.demo_interval and not self.lava_tiles:
            # Generate random tiles
            self.lava_tiles = set()
            for _ in range(self.demo_tiles_num):
                self.lava_tiles.add((random.randrange(self.rows), random.randrange(self.cols)))
            self.last_demo_time = now

    async def run(self):
        server = await websockets.serve(self.handler, '0.0.0.0', self.port)
        logger.info(f'Robust WebSocket server listening on ws://0.0.0.0:{self.port}')
        fps_time = time.time()
        fps_counter = 0
        fps_value = 0.0
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    await asyncio.sleep(0.005)
                    continue
                
                self.frame_id += 1
                self.smoother.next_frame()

                # Detect marker boundaries for constraint
                self._detect_marker_boundaries(frame)

                # Detect persons and their feet
                person_feet_data = self._detect_person_feet(frame)

                # Check for lava collisions
                collision_events = self._check_lava_collisions(person_feet_data)

                # Broadcast detection frame
                payload = {
                    'type': 'detection_frame',
                    'timestamp': int(time.time() * 1000),
                    'frame_id': self.frame_id,
                    'game_active': self.game_active,
                    'collision_detected': self.collision_detected,
                    'collision_message': self.collision_message,
                    'persons': person_feet_data
                }
                await self.broadcast(payload)

                # Broadcast collision events
                for event in collision_events:
                    await self.broadcast(event)

                # Visualization using robust methods
                vis = frame.copy()
                vis = robust_visualize.draw_constrained_grid(vis, self.mapper, color=(0, 255, 0), thickness=3)
                vis = robust_visualize.draw_constrained_lava_tiles(vis, self.lava_tiles, self.mapper, alpha=0.35)
                vis = robust_visualize.draw_marker_boundaries(vis, self.mapper, color=(255, 0, 0), thickness=2)
                
                # Draw persons and their feet
                vis_players = [{
                    'player_id': p['person_id'],
                    'left': p['left_foot'],
                    'right': p['right_foot'],
                    'centroid': p['centroid']
                } for p in person_feet_data]
                vis = robust_visualize.draw_players(vis, vis_players)

                # Add game status
                status_text = f"Frame: {self.frame_id} | Persons: {len(person_feet_data)}"
                if not self.game_active:
                    status_text += " | GAME PAUSED"
                
                cv2.putText(vis, status_text, (10, 25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Add collision message
                if self.collision_detected and self.game_active:
                    cv2.putText(vis, self.collision_message, (10, 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    cv2.putText(vis, "Press SPACE to restart game", (10, 80), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
                # Add instructions
                if self.game_active:
                    cv2.putText(vis, "Red areas = LAVA! Step carefully!", (10, 110), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                else:
                    cv2.putText(vis, "Press SPACE to restart", (10, 110), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                fps_counter += 1
                now = time.time()
                if now - fps_time >= 1.0:
                    fps_value = fps_counter / (now - fps_time)
                    fps_counter = 0
                    fps_time = now
                vis = robust_visualize.draw_fps(vis, fps_value)
                vis = robust_visualize.draw_latency(vis, int((time.time() - now) * 1000))

                cv2.imshow('Robust Floor is Lava', vis)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord(' '):  # Space key to restart
                    if self.collision_detected:
                        self.game_active = True
                        self.collision_detected = False
                        self.collision_message = ""
                        logger.info("Game restarted by space key")

                self._maybe_demo_tiles()
                await asyncio.sleep(0)
        finally:
            server.close()
            await server.wait_closed()
            self.cap.release()
            self.pose.close()
            cv2.destroyAllWindows()

def main():
    with open('config.yaml', 'r') as f:
        cfg = yaml.safe_load(f)
    server = RobustLavaServer(cfg)
    asyncio.run(server.run())

if __name__ == '__main__':
    main()