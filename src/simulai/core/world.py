from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from simulai.environment.grid import Grid
from simulai.agents.base import Agent

@dataclass
class World:
    grid: Grid
    agents: List[Agent] = field(default_factory=list)
    tick: int = 0

    def add_agent(self, agent: Agent):
        self.agents.append(agent)
        self.grid.place(agent.x, agent.y, agent)

    def step(self):
        self.tick += 1
        for agent in list(self.agents):
            agent.tick(self)
