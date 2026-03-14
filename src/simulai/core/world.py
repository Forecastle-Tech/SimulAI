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

    def add_agent(self, agent) -> None:
        self.agents.append(agent)
        self.grid.place(agent.x, agent.y, agent)

    def sprinkle_food(self, count: int = 3) -> None:
        empty_cells = []

        for y in range(self.grid.height):
            for x in range(self.grid.width):
                if self.grid.get(x, y) is None:
                    empty_cells.append((x, y))

        if not empty_cells:
            return

        random.shuffle(empty_cells)

        for x, y in empty_cells[:count]:
            self.grid.place(x, y, Food())

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
