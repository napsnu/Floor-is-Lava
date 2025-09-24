from typing import Dict, List


class PoseTracker:
    def __init__(self):
        # Minimal stub for tests/integration; replace with real MediaPipe wrapper.
        pass

    def process(self, frame) -> List[Dict]:
        """
        Return a list of detections. Each detection is a dict:
        {
          'left':  {'pixel': [x, y], 'confidence': 0.0},
          'right': {'pixel': [x, y], 'confidence': 0.0},
        }
        This stub returns empty list; server/tracker handle absence.
        """
        return []

    def close(self):
        pass



