#!/usr/bin/env python3
"""
Simple client to test the updated server.
This client connects to the server and displays game state.
"""

import asyncio
import json
import websockets
import cv2
import numpy as np

class LavaGameClient:
    def __init__(self, server_url="ws://localhost:8765"):
        self.server_url = server_url
        self.websocket = None
        self.game_state = {
            'game_active': True,
            'collision_detected': False,
            'collision_message': "",
            'persons': []
        }
    
    async def connect(self):
        """Connect to the server."""
        try:
            self.websocket = await websockets.connect(self.server_url)
            print(f"Connected to {self.server_url}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    async def send_restart(self):
        """Send restart game message to server."""
        if self.websocket:
            message = {
                'type': 'restart_game'
            }
            await self.websocket.send(json.dumps(message))
            print("Sent restart game message")
    
    async def send_lava_tiles(self, lava_tiles):
        """Send lava tiles update to server."""
        if self.websocket:
            message = {
                'type': 'tile_update',
                'lava_tiles': list(lava_tiles)
            }
            await self.websocket.send(json.dumps(message))
            print(f"Sent lava tiles: {lava_tiles}")
    
    async def listen(self):
        """Listen for messages from server."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
        except Exception as e:
            print(f"Error listening: {e}")
    
    async def handle_message(self, data):
        """Handle incoming messages from server."""
        if data.get('type') == 'detection_frame':
            self.game_state['game_active'] = data.get('game_active', True)
            self.game_state['collision_detected'] = data.get('collision_detected', False)
            self.game_state['collision_message'] = data.get('collision_message', "")
            self.game_state['persons'] = data.get('persons', [])
            
            # Print game state
            if self.game_state['collision_detected']:
                print(f"🔥 {self.game_state['collision_message']}")
            
            if self.game_state['persons']:
                for person in self.game_state['persons']:
                    person_id = person['person_id']
                    left_foot = person['left_foot']
                    right_foot = person['right_foot']
                    print(f"Person {person_id}: Left foot at grid {left_foot['grid']}, Right foot at grid {right_foot['grid']}")
        
        elif data.get('type') == 'event_on_lava':
            person_id = data.get('person_id')
            foot = data.get('foot')
            grid = data.get('grid')
            print(f"🔥 COLLISION EVENT: Person {person_id} {foot} foot stepped into lava at grid {grid}")

async def main():
    client = LavaGameClient()
    
    if not await client.connect():
        return
    
    print("Client connected. Commands:")
    print("  'r' - Restart game")
    print("  'l' - Toggle lava tiles")
    print("  'q' - Quit")
    print("  'space' - Restart game (same as 'r')")
    
    # Start listening in background
    listen_task = asyncio.create_task(client.listen())
    
    try:
        while True:
            # Check for keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r') or key == ord(' '):
                await client.send_restart()
            elif key == ord('l'):
                # Toggle lava tiles
                lava_tiles = {(0, 0), (1, 1)} if len(client.game_state.get('persons', [])) == 0 else {(0, 1), (1, 0)}
                await client.send_lava_tiles(lava_tiles)
            
            await asyncio.sleep(0.01)  # Small delay to prevent high CPU usage
    
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        listen_task.cancel()
        if client.websocket:
            await client.websocket.close()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    asyncio.run(main())
