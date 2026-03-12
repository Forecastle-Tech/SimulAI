from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
import random
from simulai.environment.grid import Grid
from simulai.environment.resources import Food
from simulai.agents.base import Agent

@dataclass
class World:
    grid: Grid
    agents: List[Agent] = field(default_factory=list)
    tick: int = 0

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

    def step(self):
        self.tick += 1
        # occasionally spawn food to keep things lively
        if self.tick % 7 == 0:
            self.sprinkle_food(count=random.choice([1, 2]))
        for agent in list(self.agents):
            agent.tick(self)
