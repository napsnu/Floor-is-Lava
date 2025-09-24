# WebSocket Protocol and JSON Messages

All messages are JSON. The server broadcasts detection frames and lava events, and accepts tile updates.

## Detection Frame (Server → Clients)
```
{
  "type": "detection_frame",
  "timestamp": 1690000000000,
  "frame_id": 123,
  "players": [
    {
      "player_id": 1,
      "left": {"pixel":[350,600], "grid":[3,4], "confidence":0.92, "oob": false},
      "right": {"pixel":[370,600], "grid":[3,5], "confidence":0.90, "oob": false}
    }
  ]
}
```
- `timestamp`: epoch ms
- `frame_id`: monotonically increasing integer
- `players`: zero or more players, each with `player_id` and left/right foot states
  - `oob`: true if the foot maps outside the playable grid

## On-Lava Event (Server → Clients)
```
{
  "type": "event_on_lava",
  "timestamp": 1690000000000,
  "player_id": 1,
  "foot": "left",
  "grid": [3,4],
  "consecutive_frames": 3
}
```
- Emitted when a foot has been on a lava tile for K consecutive frames

## Tile Update (Clients → Server)
```
{
  "type": "tile_update",
  "lava_tiles": [[2,3],[4,6]]
}
```
- Replaces the set of active lava tiles.

## UDP Mirror (Optional)
- Server can optionally send the same `detection_frame` and `event_on_lava` messages via UDP to `udp.host:udp.port` in `config.yaml`.
- Messages are newline-delimited JSON strings.

## Notes
- Grid coordinates are `[row, col]` with origin at top-left of the play area.
- Grid is 2x2 (4 quadrants): [0,0], [0,1], [1,0], [1,1]
- Pixels are `[x, y]` in image coordinates.
- Feet confidence is derived from MediaPipe visibility scores. 