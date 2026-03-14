from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Memory:
    """
    Stores agent memories including food locations and social affinity.
    """

    last_food: Optional[Tuple[int, int]] = None
    food_locations: List[Tuple[int, int]] = field(default_factory=list)
    friend_affinity: Dict[str, float] = field(default_factory=dict)

    DECAY: float = 0.02
    MAX_FOOD_LOCATIONS: int = 5

    def remember_food(self, x: int, y: int) -> None:
        """
        Remember a food location. Maintains a bounded list of recent
        food discoveries.
        """
        location = (x, y)
        self.last_food = location

        if location in self.food_locations:
            self.food_locations.remove(location)

        self.food_locations.append(location)

        if len(self.food_locations) > self.MAX_FOOD_LOCATIONS:
            self.food_locations = self.food_locations[-self.MAX_FOOD_LOCATIONS :]

    def best_food_location(
        self, current_pos: Tuple[int, int] | None = None
    ) -> Optional[Tuple[int, int]]:
        """
        Return the best remembered food location.

        If current_pos is provided, the nearest remembered food is returned.
        Otherwise the most recently discovered food is returned.
        """
        if not self.food_locations:
            return None

        if current_pos is None:
            return self.food_locations[-1]

        cx, cy = current_pos
        best = None
        best_dist = float("inf")

        for fx, fy in self.food_locations:
            d = abs(cx - fx) + abs(cy - fy)

            if d < best_dist:
                best_dist = d
                best = (fx, fy)

        return best

    def update_affinity(self, name: str, delta: float) -> None:
        """
        Update social affinity toward another agent.
        """
        self.friend_affinity[name] = self.friend_affinity.get(name, 0.0) + delta

    def get_affinity(self, name: str) -> float:
        """
        Retrieve affinity value toward another agent.
        """
        return self.friend_affinity.get(name, 0.0)

    def decay(self) -> None:
        """
        Gradually decay social affinity values toward neutral.
        """
        for k in list(self.friend_affinity.keys()):
            v = self.friend_affinity[k]

            if v > 0:
                v = max(0.0, v - self.DECAY)
            elif v < 0:
                v = min(0.0, v + self.DECAY)

            if abs(v) < 1e-3:
                v = 0.0

            self.friend_affinity[k] = v
