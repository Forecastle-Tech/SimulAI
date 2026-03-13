from __future__ import annotations
import random
from typing import Tuple, Optional
from simulai.agents.base import Agent
from simulai.agents.traits import Traits
from simulai.agents.emotions import EmotionState, compute_emotion
from simulai.environment.resources import Food

DIRECTIONS = [(0,1),(0,-1),(1,0),(-1,0)]

POSITIVE_QUIPS = [
    "Nice to see you!", "What a fine day!", "High five!", "You look radiant today!"
]
NEGATIVE_QUIPS = [
    "Meh.", "Watch it.", "Not in the mood.", "Hmm."
]

class Simulite(Agent):
    """A tiny AI creature with simple needs, personality, and a dash of attitude."""
    def __init__(self, name: str, x: int, y: int, traits: Optional[Traits] = None):
        super().__init__(name, x, y)
        self.energy = 10
        self.mood = 0.0  # ~ -5..+5 (soft cap)
        self.traits = traits or Traits.random()
        self.emotion: EmotionState | None = None
        self._recent_event: str | None = None  # used to compute emotion per tick

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
            # circular import safe because we reference class name string
            from simulai.agents.simulite import Simulite as S
            if isinstance(cell, S) and cell is not self:
                return (nx, ny)
        return None

    # ---- Turn logic -------------------------------------------------------
    def tick(self, world):
        self._recent_event = None
        # 1) Passive energy drain
        self.energy -= 1

        # 2) If out of energy, nap
        if self.energy <= 0:
            self.energy = 6  # nap restores energy
            self.mood = max(-5, self.mood - 1)
            world.grid.place(self.x, self.y, self)  # stay put
            self._recent_event = "nap"
            world._last_log = f"{self.name} takes a nap."
            world._last_mood = self.mood
            self._update_emotion(world)
            return

        # 3) Eat if food is adjacent
        food_loc = self.find_adjacent_food(world)
        if food_loc:
            fx, fy = food_loc
            world.grid.move(self.x, self.y, fx, fy)
            self.x, self.y = fx, fy
            self.energy = min(15, self.energy + 5)
            self.mood = min(5, self.mood + 1.5)
            self._recent_event = "eat"
            world._last_log = f"{self.name} munches on food at ({fx},{fy})."
            world._last_mood = self.mood
            self._update_emotion(world)
            return

        # 4) Social interaction if adjacent + sociable
        friend_loc = self.find_adjacent_friend(world)
        if friend_loc and self.traits.sociability >= 6:
            fx, fy = friend_loc
            friend = world.grid.get(fx, fy)
            if friend is not None and isinstance(friend, Simulite):
                # Positive or negative interaction depends on your mood
                if self.mood >= 0:
                    self.mood = min(5, self.mood + 0.5)
                    friend.mood = min(5, friend.mood + 0.4)
                    quip = random.choice(POSITIVE_QUIPS)
                    self._recent_event = "social_pos"
                    world._last_log = f"{self.name} to {friend.name}: “{quip}”"
                else:
                    self.mood = max(-5, self.mood + 0.2)  # socializing helps a tad
                    friend.mood = max(-5, friend.mood - 0.2)
                    quip = random.choice(NEGATIVE_QUIPS)
                    self._recent_event = "social_neg"
                    world._last_log = f"{self.name} to {friend.name}: “{quip}”"
                world._last_mood = self.mood
                self._update_emotion(world)
                return

        # 5) Wander — curiosity boosts number of attempts
        attempts = 1 + (self.traits.curiosity // 4)  # 1..3 tries
        for _ in range(attempts):
            dx, dy = random.choice(DIRECTIONS)
            nx, ny = self.x + dx, self.y + dy
            if world.grid.in_bounds(nx, ny) and world.grid.get(nx, ny) is None:
                world.grid.move(self.x, self.y, nx, ny)
                self.x, self.y = nx, ny
                self.mood = min(5, self.mood + 0.4)
                world._last_log = f"{self.name} explores to ({nx},{ny})."
                world._last_mood = self.mood
                self._recent_event = None
                self._update_emotion(world)
                return

        # 6) If blocked, mood dips
        self.mood = max(-5, self.mood - 0.5)
        world._last_log = f"{self.name} feels stuck."
        world._last_mood = self.mood
        self._recent_event = "blocked"
        self._update_emotion(world)

    def _update_emotion(self, world):
        self.emotion = compute_emotion(self.energy, self.mood, self._recent_event)
        world._last_emotion = str(self.emotion)
