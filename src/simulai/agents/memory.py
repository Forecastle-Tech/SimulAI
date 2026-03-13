from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

@dataclass
class Memory:
    """Lightweight memory for Simulites.
    - last_food: last known food coordinates (they'll try to return when hungry)
    - friend_affinity: map of friend name -> affinity score (-3..+3)
    """
    last_food: Optional[Tuple[int, int]] = None
    friend_affinity: Dict[str, float] = field(default_factory=dict)

    AFFINITY_MIN: float = -3.0
    AFFINITY_MAX: float = 3.0
    DECAY: float = 0.05  # per tick, affinity moves towards 0
    FOOD_FORGET_DECAY: float = 0.02  # chance to forget food each tick (soft)

    def remember_food(self, x: int, y: int):
        self.last_food = (x, y)

    def forget_food_soft(self):
        # Soft forgetting: occasionally clear last food (stochastic feel)
        # For reproducibility/stability we implement a small deterministic decay:
        # After ~50 ticks (2% decay per tick) you'd likely forget.
        # Here, simulate decay by a counterless approach: leave as-is; world logic can overwrite.
        pass

    def update_affinity(self, name: str, delta: float):
        cur = self.friend_affinity.get(name, 0.0)
        cur += delta
        cur = max(self.AFFINITY_MIN, min(self.AFFINITY_MAX, cur))
        self.friend_affinity[name] = cur
        return cur

    def get_affinity(self, name: str) -> float:
        return self.friend_affinity.get(name, 0.0)

    def decay(self):
        # Move all affinities gently towards 0
        if not self.friend_affinity:
            return
        for k, v in list(self.friend_affinity.items()):
            if v > 0:
                v = max(0.0, v - self.DECAY)
            elif v < 0:
                v = min(0.0, v + self.DECAY)
            # Clean near-zero noise
            if abs(v) < 1e-3:
                v = 0.0
            self.friend_affinity[k] = v
``
