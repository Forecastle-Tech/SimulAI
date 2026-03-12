from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Food:
    energy: int = 5

    def __repr__(self) -> str:
        return f"Food(+{self.energy})"
