from __future__ import annotations

import random
from typing import Any, Optional


class Grid:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells = [[None for _ in range(width)] for _ in range(height)]

        # Zone map for ecosystem behavior
        self.zones = [["plains" for _ in range(width)] for _ in range(height)]
        self._build_default_zones()

    def _build_default_zones(self) -> None:
        """
        Simple first zone layout:
        - left third: forest
        - middle third: plains
        - right third: drylands
        - small village patch in the center
        """
        left_cut = self.width // 3
        right_cut = (2 * self.width) // 3

        for y in range(self.height):
            for x in range(self.width):
                if x < left_cut:
                    self.zones[y][x] = "forest"
                elif x >= right_cut:
                    self.zones[y][x] = "drylands"
                else:
                    self.zones[y][x] = "plains"

        # Add a small central village zone
        cx = self.width // 2
        cy = self.height // 2
        for y in range(max(0, cy - 1), min(self.height, cy + 2)):
            for x in range(max(0, cx - 1), min(self.width, cx + 2)):
                self.zones[y][x] = "village"

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
            (x, y) for y in range(self.height) for x in range(self.width) if self.get(x, y) is None
        ]
        return random.choice(empties) if empties else None

    def get_zone(self, x: int, y: int) -> str:
        if not self.in_bounds(x, y):
            return "plains"
        return self.zones[y][x]

    def set_zone(self, x: int, y: int, zone_name: str) -> None:
        if self.in_bounds(x, y):
            self.zones[y][x] = zone_name

    def cells_in_zone(self, zone_name: str) -> list[tuple[int, int]]:
        return [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.zones[y][x] == zone_name
        ]

    def random_cell_in_zone(self, zone_name: str) -> Optional[tuple[int, int]]:
        cells = self.cells_in_zone(zone_name)
        return random.choice(cells) if cells else None
