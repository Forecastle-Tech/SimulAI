from __future__ import annotations
import random
from simulai.agents.base import Agent

DIRECTIONS = [(0,1),(0,-1),(1,0),(-1,0)]

class Simulite(Agent):
    """A tiny AI creature with simple needs and a dash of attitude."""
    def __init__(self, name: str, x: int, y: int):
        super().__init__(name, x, y)
        self.energy = 10
        self.mood = 0  # -5..+5

    def tick(self, world):
        # energy drains each tick; if empty, nap (stay put), mood drops
        self.energy -= 1
        if self.energy <= 0:
            self.energy = 5  # nap restores some energy
            self.mood -= 1
            world.grid.place(self.x, self.y, self)
            world._last_log = f"{self.name} takes a nap. 😴"
            return

        # otherwise wander to a random adjacent free cell
        dx, dy = random.choice(DIRECTIONS)
        nx, ny = self.x + dx, self.y + dy
        if world.grid.in_bounds(nx, ny) and world.grid.get(nx, ny) is None:
            world.grid.move(self.x, self.y, nx, ny)
            self.x, self.y = nx, ny
            self.mood = min(5, self.mood + 1)
            world._last_log = f"{self.name} wanders to ({nx},{ny}). 🐾"
        else:
            self.mood = max(-5, self.mood - 1)
            world._last_log = f"{self.name} bumps into something. 😤"
