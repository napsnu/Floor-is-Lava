from typing import Dict, Tuple


class LavaSmoother:
    def __init__(self, k_consecutive: int = 3, m_clear: int = 2):
        """
        Debounce lava detection by requiring K consecutive lava frames to trigger,
        and M consecutive safe frames to clear.

        Trigger semantics: returns True only on the frame that reaches K
        consecutive lava observations for a given (player_id, foot).
        """
        self.k = int(k_consecutive)
        self.m = int(m_clear)
        # state[(player_id, foot)] = {
        #   'last_frame': int,
        #   'lava_run': int,
        #   'safe_run': int,
        #   'is_on_lava': bool,
        #   'last_cell': Tuple[int, int],
        # }
        self.state: Dict[Tuple[int, str], Dict] = {}
        self.frame_index = 0

    def next_frame(self) -> None:
        self.frame_index += 1

    def observe(self, player_id: int, foot: str, row: int, col: int, is_lava: bool) -> bool:
        key = (int(player_id), str(foot))
        if key not in self.state:
            self.state[key] = {
                'last_frame': self.frame_index,
                'lava_run': 0,
                'safe_run': 0,
                'is_on_lava': False,
                'last_cell': (int(row), int(col)),
            }

        s = self.state[key]
        s['last_cell'] = (int(row), int(col))
        s['last_frame'] = self.frame_index

        # Update runs
        if is_lava:
            s['lava_run'] += 1
            s['safe_run'] = 0
        else:
            s['safe_run'] += 1
            s['lava_run'] = 0

        triggered = False

        # Trigger when crossing the threshold and currently not flagged
        if is_lava and (not s['is_on_lava']) and s['lava_run'] >= self.k:
            s['is_on_lava'] = True
            triggered = True

        # Clear when enough safe frames observed
        if s['is_on_lava'] and (not is_lava) and s['safe_run'] >= self.m:
            s['is_on_lava'] = False

        return triggered



