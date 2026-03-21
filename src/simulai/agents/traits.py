from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Traits:
    curiosity: float = 5.0
    sociability: float = 5.0
    discipline: float = 5.0
    resilience: float = 5.0
    metabolism: float = 5.0
    kindness: float = 5.0
    caution: float = 5.0

    def clamp(self) -> None:
        self.curiosity = max(0.0, min(10.0, self.curiosity))
        self.sociability = max(0.0, min(10.0, self.sociability))
        self.discipline = max(0.0, min(10.0, self.discipline))
        self.resilience = max(0.0, min(10.0, self.resilience))
        self.metabolism = max(0.0, min(10.0, self.metabolism))
        self.kindness = max(0.0, min(10.0, self.kindness))
        self.caution = max(0.0, min(10.0, self.caution))
