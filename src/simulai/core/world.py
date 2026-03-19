from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List

from simulai.environment.resources import Food


@dataclass
class Weather:
    kind: str = "clear"
    icon: str = "☀️"
    duration: int = 5

    def step(self) -> None:
        self.duration -= 1
        if self.duration <= 0:
            self._roll_next()

    def _roll_next(self) -> None:
        options = [
            ("clear", "☀️", random.randint(4, 6)),
            ("cloudy", "☁️", random.randint(3, 5)),
            ("breezy", "🍃", random.randint(3, 5)),
            ("rainy", "🌧️", random.randint(3, 5)),
        ]
        self.kind, self.icon, self.duration = random.choice(options)


class World:
    def __init__(self, grid):
        self.grid = grid
        self.agents: List = []
        self.tick = 0

        self.weather = Weather()

        self._last_log = ""
        self._last_mood = 0.0
        self._last_emotion = ""
        self._last_goal = ""

        self.food_regrow_interval = 12
        self.food_regrow_amount = 2
        self.max_agents = 20
        self._next_agent_id = 1

        self.food_zones = self._build_food_zones()

    def _build_food_zones(self) -> list[dict]:
        width = self.grid.width
        height = self.grid.height

        return [
            {
                "name": "forest",
                "x1": 0,
                "y1": 0,
                "x2": max(1, width // 3),
                "y2": height - 1,
                "weight": 0.6,
                "patch_size": (3, 5),
            },
            {
                "name": "plains",
                "x1": max(1, width // 3),
                "y1": 0,
                "x2": max(2, (2 * width) // 3),
                "y2": height - 1,
                "weight": 0.3,
                "patch_size": (2, 3),
            },
            {
                "name": "desert",
                "x1": max(2, (2 * width) // 3),
                "y1": 0,
                "x2": width - 1,
                "y2": height - 1,
                "weight": 0.1,
                "patch_size": (1, 2),
            },
        ]

    def next_agent_name(self, parent_name: str = "Sim") -> str:
        name = f"{parent_name}-{self._next_agent_id}"
        self._next_agent_id += 1
        return name

    def add_agent(self, agent) -> None:
        self.agents.append(agent)
        self.grid.place(agent.x, agent.y, agent)

    def _empty_cells_in_zone(self, zone: dict) -> list[tuple[int, int]]:
        cells = []

        for y in range(zone["y1"], zone["y2"] + 1):
            for x in range(zone["x1"], zone["x2"] + 1):
                if self.grid.in_bounds(x, y) and self.grid.get(x, y) is None:
                    cells.append((x, y))

        return cells

    def _place_food_if_empty(self, x: int, y: int) -> bool:
        if not self.grid.in_bounds(x, y):
            return False
        if self.grid.get(x, y) is not None:
            return False

        self.grid.place(x, y, Food())
        return True

    def _spawn_food_patch(self, zone: dict, patch_cells: int) -> int:
        empty_cells = self._empty_cells_in_zone(zone)
        if not empty_cells:
            return 0

        seed_x, seed_y = random.choice(empty_cells)
        placed = 0

        if self._place_food_if_empty(seed_x, seed_y):
            placed += 1

        candidates = [
            (seed_x + 1, seed_y),
            (seed_x - 1, seed_y),
            (seed_x, seed_y + 1),
            (seed_x, seed_y - 1),
            (seed_x + 1, seed_y + 1),
            (seed_x - 1, seed_y - 1),
            (seed_x + 1, seed_y - 1),
            (seed_x - 1, seed_y + 1),
        ]
        random.shuffle(candidates)

        for x, y in candidates:
            if placed >= patch_cells:
                break
            if (
                zone["x1"] <= x <= zone["x2"]
                and zone["y1"] <= y <= zone["y2"]
                and self._place_food_if_empty(x, y)
            ):
                placed += 1

        return placed

    def sprinkle_food(self, count: int = 3) -> None:
        if count <= 0:
            return

        placed_total = 0
        max_attempts = count * 6
        attempts = 0

        while placed_total < count and attempts < max_attempts:
            attempts += 1

            zone = random.choices(
                self.food_zones,
                weights=[z["weight"] for z in self.food_zones],
                k=1,
            )[0]

            min_patch, max_patch = zone["patch_size"]
            patch_cells = random.randint(min_patch, max_patch)

            remaining = count - placed_total
            patch_cells = min(patch_cells, remaining)

            placed = self._spawn_food_patch(zone, patch_cells)
            if placed == 0:
                continue

            placed_total += placed

    def step(self) -> None:
        self.tick += 1

        self.weather.step()

        self._last_log = ""
        self._last_goal = ""

        for agent in list(self.agents):
            agent.tick(self)

        if self.tick % self.food_regrow_interval == 0:
            self.sprinkle_food(self.food_regrow_amount)
            self._last_log = "New food sprouted."

    def summary(self) -> str:
        return (
            f"SimulAI — tick {self.tick}   "
            f"Weather: {self.weather.icon} "
            f"{self.weather.kind} ({self.weather.duration})"
        )
