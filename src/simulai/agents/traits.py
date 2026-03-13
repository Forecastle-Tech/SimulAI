from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class Traits:
    """Basic personality traits for Simulites.

    - curiosity: how likely they are to explore (0..10)
    - sociability: how likely they are to approach others (0..10)
    """

    curiosity: int
    sociability: int

    @classmethod
    def random(cls) -> "Traits":
        # Mildly biased toward middle values
        curiosity = random.randint(0, 10)
        sociability = random.randint(0, 10)
        return cls(curiosity=curiosity, sociability=sociability)
