from __future__ import annotations
import random
from typing import Tuple, Optional
from simulai.agents.base import Agent
from simulai.agents.traits import Traits
from simulai.environment.resources import Food

DIRECTIONS = [(0,1),(0,-1),(1,0),(-1,0)]

class Simulite(Agent):
    """A tiny AI creature with simple needs, personality, and a dash of attitude."""
    def __init__(self, name: str, x: int, y: int, traits: Optional[Traits] = None):
        super().__init__(name, x, y)
        self.energy = 10
        self.mood = 0  # ~ -5..+5 (soft cap)
        self.traits = traits or Traits.random()

    # ---- Decision helpers -------------------------------------------------
    def neighbors(self, world) -> list[Tuple[int, int]]:
        out = []
        for dx, dy in DIRECTIONS:
            nx, ny = self.x + dx, self.y + dy
            if world.grid.in_bounds(nx, ny):
                out.append((nx, ny))
        return out

    def find_adjacent_food(self, world) -> Optional[Tuple[int, int]]:
        for (nx, ny) in self.neighbors(world):
            cell = world.grid.get(nx, ny)
            if isinstance(cell, Food):
                return (nx, ny)
        return None

    def find_adjacent_friend(self, world) -> Optional[Tuple[int, int]]:
        for (nx, ny) in self.neighbors(world):
            cell = world.grid.get(nx, ny)
            if isinstance(cell, Simulite) and cell is not self:
                return (nx, ny)
        return None

    # ---- Turn logic -------------------------------------------------------
    def tick(self, world):
        # 1) Passive effects
        self.energy -= 1

        # 2) If out of energy, nap
        if self.energy <= 0:
            self.energy = 6  # nap restores energy
            self.mood = max(-5, self.mood - 1)
            world.grid.place(self.x, self.y, self)  # stay put
            world._last_log = f"{self.name} takes a nap."
            world._last_mood = self.mood
            return

        # 3) Eat if food is adjacent (high priority)
        food_loc = self.find_adjacent_food(world)
        if food_loc:
            fx, fy = food_loc
            # "move into" the food cell and consume it
            world.grid.move(self.x, self.y, fx, fy)
            self.x, self.y = fx, fy
            self.energy = min(15, self.energy + 5)
            self.mood = min(5, self.mood + 1.5)
            # remove the food (we overwrote the cell with ourselves on move)
            world._last_log = f"{self.name} munches on food at ({fx},{fy})."
            world._last_mood = self.mood
            return

        # 4) If sociable and someone is adjacent, interact
        friend_loc = self.find_adjacent_friend(world)
        if friend_loc and self.traits.sociability >= 6:
            # Interaction: simple mood exchange
            fx, fy = friend_loc
            friend = world.grid.get(fx, fy)
            if isinstance(friend, Simulite):
                # Cheer if in a good mood, grumble otherwise
                if self.mood >= 0:
                    self.mood = min(5, self.mood + 0.5)
                    friend.mood = min(5, friend.mood + 0.5)
                    world._last_log = f"{self.name} cheers up {friend.name}."
                else:
                    self.mood = max(-5, self.mood + 0.2)  # socializing helps a bit
                    friend.mood = max(-5, friend.mood - 0.2)
                    world._last_log = f"{self.name} grumbles at {friend.name}."
                world._last_mood = self.mood
                return

        # 5) Otherwise wander — curiosity boosts movement attempts
        attempts = 1 + (self.traits.curiosity // 4)  # 1..3 tries
        for _ in range(attempts):
            dx, dy = random.choice(DIRECTIONS)
            nx, ny = self.x + dx, self.y + dy
            if world.grid.in_bounds(nx, ny) and world.grid.get(nx, ny) is None:
                world.grid.move(self.x, self.y, nx, ny)
                self.x, self.y = nx, ny
                self.mood = min(5, self.mood + 0.5)
                world._last_log = f"{self.name} explores to ({nx},{ny})."
                world._last_mood = self.mood
                return

        # 6) If blocked, mood dips
        self.mood = max(-5, self.mood - 0.5)
        world._last_log = f"{self.name} feels stuck."
        world._last_mood = self.mood
``
