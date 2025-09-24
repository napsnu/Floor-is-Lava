import asyncio
import json
import websockets

WS_URL = 'ws://localhost:8765'


async def run():
    async with websockets.connect(WS_URL) as ws:
        print('Connected to', WS_URL)
        # send a tile update after connecting (2x2 grid: [0,0], [0,1], [1,0], [1,1])
        await ws.send(json.dumps({'type': 'tile_update', 'lava_tiles': [[0, 0], [1, 1]]}))
        while True:
            msg = await ws.recv()
            try:
                data = json.loads(msg)
            except Exception:
                print('Received non-JSON message')
                continue
            print(json.dumps(data, indent=2))


if __name__ == '__main__':
    asyncio.run(run()) 