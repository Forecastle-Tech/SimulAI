from __future__ import annotations
from typing import Optional, Any
import random

class Grid:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells = [[None for _ in range(width)] for _ in range(height)]

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> Optional[Any]:
        if not self.in_bounds(x, y):
            return None
        return self.cells[y][x]

    def place(self, x: int, y: int, obj: Any):
        if self.in_bounds(x, y):
            self.cells[y][x] = obj

    def move(self, x_from: int, y_from: int, x_to: int, y_to: int):
        if not self.in_bounds(x_to, y_to):
            return False
        obj = self.get(x_from, y_from)
        if obj is None:
            return False
        self.cells[y_from][x_from] = None
        self.cells[y_to][x_to] = obj
        return True

    def random_empty_cell(self):
        empties = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.get(x, y) is None
        ]
        return random.choice(empties) if empties else None
