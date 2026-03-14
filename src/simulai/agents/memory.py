from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Memory:
    last_food: Optional[Tuple[int, int]] = None
    food_locations: List[Tuple[int, int]] = field(default_factory=list)
    friend_affinity: Dict[str, float] = field(default_factory=dict)

    DECAY: float = 0.02
    MAX_FOOD_LOCATIONS: int = 5

    def remember_food(self, x: int, y: int) -> None:
        location = (x, y)
        self.last_food = location

        if location in self.food_locations:
            self.food_locations.remove(location)

        self.food_locations.append(location)

        if len(self.food_locations) > self.MAX_FOOD_LOCATIONS:
            self.food_locations = self.food_locations[-self.MAX_FOOD_LOCATIONS :]

    def best_food_location(self) -> Optional[Tuple[int, int]]:
        if not self.food_locations:
            return None
        return self.food_locations[-1]

    def update_affinity(self, name: str, delta: float) -> None:
        self.friend_affinity[name] = self.friend_affinity.get(name, 0.0) + delta

    def get_affinity(self, name: str) -> float:
        return self.friend_affinity.get(name, 0.0)

    def decay(self) -> None:
        for k in list(self.friend_affinity.keys()):
            v = self.friend_affinity[k]
            if v > 0:
                v = max(0.0, v - self.DECAY)
            elif v < 0:
                v = min(0.0, v + self.DECAY)
            if abs(v) < 1e-3:
                v = 0.0
            self.friend_affinity[k] = v
