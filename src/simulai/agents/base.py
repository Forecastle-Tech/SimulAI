from __future__ import annotations

from abc import ABC, abstractmethod


class Agent(ABC):
    def __init__(self, name: str, x: int, y: int):
        self.name = name
        self.x = x
        self.y = y

    @abstractmethod
    def tick(self, world): ...
