from __future__ import annotations

import random
from dataclasses import dataclass

WEATHERS = ["clear", "breezy", "cloudy", "rain", "storm"]


@dataclass
class Weather:
    kind: str = "clear"
    duration: int = 0  # ticks remaining

    def __str__(self) -> str:
        return f"{self.kind}({self.duration})"


def random_weather() -> Weather:
    kind = random.choices(WEATHERS, weights=[4, 3, 3, 2, 1], k=1)[0]
    duration = random.randint(4, 10)
    return Weather(kind=kind, duration=duration)
