from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
import random
from simulai.environment.grid import Grid
from simulai.environment.resources import Food
from simulai.environment.events import Weather, random_weather
from simulai.agents.base import Agent
from simulai.agents.simulite import Simulite

@dataclass
class World:
    grid: Grid
    agents: List[Agent] = field(default_factory=list)
    tick: int = 0
    weather: Weather = field(default_factory=random_weather)

    def add_agent(self, agent: Agent):
        self.agents.append(agent)
        self.grid.place(agent.x, agent.y, agent)

    def sprinkle_food(self, count: int = 5):
        """Place `count` Food objects at random empty cells."""
        placed = 0
        attempts = 0
        while placed < count and attempts < count * 10:
            attempts += 1
            spot = self.grid.random_empty_cell()
            if not spot:
                break
            x, y = spot
            if self.grid.get(x, y) is None:
                self.grid.place(x, y, Food())
                placed += 1

    def _advance_weather(self):
        # Decrement duration; roll new weather if expired
        self.weather.duration -= 1
        if self.weather.duration <= 0:
            self.weather = random_weather()

    def step(self):
        self.tick += 1

        # Weather cycles every tick; food sometimes spawns
        self._advance_weather()
        if self.tick % 7 == 0:
            self.sprinkle_food(count=random.choice([1, 2]))

        # Apply weather influence (simple: rain/storm reduces curiosity for Simulites)
        for agent in list(self.agents):
            if isinstance(agent, Simulite):
                if self.weather.kind in ("rain", "storm"):
                    # temporary nudge to mood/curiosity via mood
                    agent.mood = max(-5, agent.mood - 0.1)

            agent.tick(self)
