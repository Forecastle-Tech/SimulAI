from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from simulai.environment.resources import Food
from simulai.io.metrics import MetricsExporter


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
        self.agents: list[Any] = []
        self.tick = 0

        self.weather = Weather()

        self._last_log = ""
        self._last_mood = 0.0
        self._last_emotion = ""
        self._last_goal = ""

        self.food_regrow_interval = 12
        self.food_regrow_amount = 1
        self.max_agents = 20
        self._next_agent_id = 1

        self.food_zones = self._build_food_zones()

        # Ecosystem dashboard metrics
        self.total_births = 0
        self.total_deaths = 0
        self.max_generation = 0
        self.population_history: list[int] = []

        # CSV metrics export
        self.metrics_exporter = MetricsExporter()

    def _build_food_zones(self) -> list[dict]:
        """
        Build three non-intersecting polygon biomes across the grid.

        The polygons share borders but are intended not to overlap.
        Coordinates are grid-cell coordinates, not pixel coordinates.
        """
        width = self.grid.width
        height = self.grid.height

        mid_x = width // 2
        left_x = max(1, width // 3)
        right_x = min(width - 1, (2 * width) // 3)

        top_y = 0
        bottom_y = height - 1
        upper_mid_y = max(1, height // 3)
        lower_mid_y = max(2, (2 * height) // 3)

        return [
            {
                "name": "forest",
                "weight": 0.55,
                "patch_size": (3, 5),
                "polygon": [
                    (0, top_y),
                    (left_x, top_y),
                    (mid_x - 1, upper_mid_y),
                    (left_x, lower_mid_y),
                    (0, bottom_y),
                ],
            },
            {
                "name": "plains",
                "weight": 0.30,
                "patch_size": (2, 3),
                "polygon": [
                    (left_x, top_y),
                    (right_x, top_y),
                    (right_x + 1, upper_mid_y),
                    (right_x, lower_mid_y),
                    (left_x, bottom_y),
                    (mid_x - 1, lower_mid_y),
                    (mid_x - 1, upper_mid_y),
                ],
            },
            {
                "name": "desert",
                "weight": 0.15,
                "patch_size": (1, 2),
                "polygon": [
                    (right_x, top_y),
                    (width - 1, top_y),
                    (width - 1, bottom_y),
                    (right_x, bottom_y),
                    (right_x + 1, lower_mid_y),
                    (right_x + 1, upper_mid_y),
                ],
            },
        ]

    def next_agent_name(self, parent_name: str = "Sim") -> str:
        name = f"{parent_name}-{self._next_agent_id}"
        self._next_agent_id += 1
        return name

    def add_agent(self, agent) -> None:
        self.agents.append(agent)
        self.grid.place(agent.x, agent.y, agent)
        self.max_generation = max(self.max_generation, getattr(agent, "generation", 0))

    def record_birth(self, agent) -> None:
        self.total_births += 1
        self.max_generation = max(self.max_generation, getattr(agent, "generation", 0))

    def record_death(self, count: int = 1) -> None:
        self.total_deaths += count

    def record_population(self) -> None:
        self.population_history.append(len(self.agents))
        if len(self.population_history) > 200:
            self.population_history.pop(0)

    def get_population_trend(self) -> str:
        if len(self.population_history) < 2:
            return "→"

        recent = self.population_history[-1]
        older_index = max(0, len(self.population_history) - 10)
        older = self.population_history[older_index]

        if recent > older:
            return "↑"
        if recent < older:
            return "↓"
        return "→"

    def get_dashboard_stats(self) -> dict:
        return {
            "population": len(self.agents),
            "births": self.total_births,
            "deaths": self.total_deaths,
            "max_generation": self.max_generation,
            "ticks": self.tick,
            "trend": self.get_population_trend(),
            "population_history": self.population_history.copy(),
            "weather_kind": self.weather.kind,
            "weather_icon": self.weather.icon,
            "weather_duration": self.weather.duration,
        }

    def remove_dead_agents(self) -> None:
        dead_agents = [agent for agent in self.agents if not getattr(agent, "alive", True)]
        if dead_agents:
            self.record_death(len(dead_agents))

        self.agents = [agent for agent in self.agents if getattr(agent, "alive", True)]

    def _point_in_polygon(self, x: int, y: int, polygon: list[tuple[int, int]]) -> bool:
        """
        Ray-casting point-in-polygon test using cell-center coordinates.
        """
        px = x + 0.5
        py = y + 0.5

        inside = False
        j = len(polygon) - 1

        for i in range(len(polygon)):
            xi, yi = polygon[i]
            xj, yj = polygon[j]

            intersects = ((yi > py) != (yj > py)) and (
                px < (xj - xi) * (py - yi) / ((yj - yi) or 1e-9) + xi
            )
            if intersects:
                inside = not inside

            j = i

        return inside

    def _empty_cells_in_zone(self, zone: dict) -> list[tuple[int, int]]:
        cells: list[tuple[int, int]] = []

        for y in range(self.grid.height):
            for x in range(self.grid.width):
                if not self.grid.in_bounds(x, y):
                    continue
                if self.grid.get(x, y) is not None:
                    continue
                if self._point_in_polygon(x, y, zone["polygon"]):
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
            if self.grid.in_bounds(x, y) and self._point_in_polygon(x, y, zone["polygon"]):
                if self._place_food_if_empty(x, y):
                    placed += 1

        return placed

    def sprinkle_food(self, count: int = 3) -> None:
        if count <= 0:
            return

        placed_total = 0
        max_attempts = count * 8
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
            patch_cells = min(patch_cells, count - placed_total)

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

        self.remove_dead_agents()

        if self.tick % self.food_regrow_interval == 0:
            self.sprinkle_food(self.food_regrow_amount)
            self._last_log = "New food sprouted."

        self.record_population()

        if self.metrics_exporter is not None:
            self.metrics_exporter.record(self)

    def summary(self) -> str:
        return (
            f"SimulAI — tick {self.tick}   "
            f"Weather: {self.weather.icon} "
            f"{self.weather.kind} ({self.weather.duration})"
        )
