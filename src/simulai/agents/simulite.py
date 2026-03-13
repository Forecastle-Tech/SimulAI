from __future__ import annotations

import random
from typing import List, Optional, Tuple

from simulai.agents.base import Agent
from simulai.agents.emotions import EmotionState, compute_emotion
from simulai.agents.goals import (
    Goal,
    GreetFavoriteFriend,
    VisitRememberedFood,
    build_eat_then_greet_sequence,
)
from simulai.agents.memory import Memory
from simulai.agents.traits import Traits
from simulai.environment.resources import Food

DIRECTIONS: List[Tuple[int, int]] = [(0, 1), (0, -1), (1, 0), (-1, 0)]

POSITIVE_QUIPS = [
    "Nice to see you!",
    "What a fine day!",
    "High five!",
    "You look radiant today!",
]
NEGATIVE_QUIPS = [
    "Meh.",
    "Watch it.",
    "Not in the mood.",
    "Hmm.",
]


class Simulite(Agent):
    """A tiny AI creature with simple needs, personality, memory, goals, and a dash of attitude."""

    def __init__(self, name: str, x: int, y: int, traits: Optional[Traits] = None):
        super().__init__(name, x, y)
        self.energy = 10
        self.mood = 0.0  # ~ -5..+5 (soft cap)
        self.traits = traits or Traits.random()
        self.emotion: EmotionState | None = None
        self._recent_event: str | None = None  # used to compute emotion per tick
        self.memory = Memory()

        # Goals
        self.goal: Optional[Goal] = None
        self._goal_cooldown = 0  # ticks until we may switch/choose a new goal

    # ---- Helpers ----------------------------------------------------------
    def neighbors(self, world) -> list[Tuple[int, int]]:
        out: list[Tuple[int, int]] = []
        for dx, dy in DIRECTIONS:
            nx, ny = self.x + dx, self.y + dy
            if world.grid.in_bounds(nx, ny):
                out.append((nx, ny))
        return out

    def manhattan(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def choose_step_towards(
        self, world, target: Tuple[int, int]
    ) -> Optional[Tuple[int, int]]:
        """Pick a neighbor step that reduces Manhattan distance to target and is empty."""
        cur = (self.x, self.y)
        best: list[Tuple[int, int]] = []
        best_d = self.manhattan(cur, target)
        for dx, dy in DIRECTIONS:
            nx, ny = self.x + dx, self.y + dy
            if not world.grid.in_bounds(nx, ny):
                continue
            if world.grid.get(nx, ny) is not None:
                continue
            d = self.manhattan((nx, ny), target)
            if d < best_d:
                best = [(nx, ny)]
                best_d = d
            elif d == best_d:
                best.append((nx, ny))
        if best:
            return random.choice(best)
        return None

    def choose_step_away_from(
        self, world, from_pos: Tuple[int, int]
    ) -> Optional[Tuple[int, int]]:
        """Pick a neighbor step that increases distance from from_pos and is empty."""
        cur = (self.x, self.y)
        cur_d = self.manhattan(cur, from_pos)
        candidates: list[Tuple[int, int]] = []
        for dx, dy in DIRECTIONS:
            nx, ny = self.x + dx, self.y + dy
            if not world.grid.in_bounds(nx, ny):
                continue
            if world.grid.get(nx, ny) is not None:
                continue
            d = self.manhattan((nx, ny), from_pos)
            if d > cur_d:
                candidates.append((nx, ny))
        if candidates:
            return random.choice(candidates)
        return None

    def find_adjacent_food(self, world) -> Optional[Tuple[int, int]]:
        for nx, ny in self.neighbors(world):
            cell = world.grid.get(nx, ny)
            if isinstance(cell, Food):
                return (nx, ny)
        return None

    def find_adjacent_friend(self, world) -> Optional[Tuple[int, int]]:
        for nx, ny in self.neighbors(world):
            cell = world.grid.get(nx, ny)
            if isinstance(cell, Simulite) and cell is not self:
                return (nx, ny)
        return None

    # ---- Goal selection ---------------------------------------------------
    def _favorite_friend_name(self) -> Optional[str]:
        if not self.memory.friend_affinity:
            return None
        best_name = None
        best_val = 0.8
        for k, v in self.memory.friend_affinity.items():
            if v > best_val:
                best_val = v
                best_name = k
        return best_name

    def consider_goals(self, world):
        """Pick a goal based on current state, memory, and cooldown."""
        if self._goal_cooldown > 0:
            self._goal_cooldown -= 1
            return

        if self.goal and not self.goal.done():
            return

        candidates: List[Goal] = []

        # Prefer CHAIN: Eat -> then Greet (if hungry and food remembered)
        if self.memory.last_food is not None and self.energy <= 7:
            seq = build_eat_then_greet_sequence(self)
            if seq and seq.can_start(self, world):
                candidates.append(seq)

        # Fallback individual goals
        visit_food = VisitRememberedFood()
        if visit_food.can_start(self, world):
            candidates.append(visit_food)

        fav = self._favorite_friend_name()
        if fav and self.traits.sociability >= 6:
            greet = GreetFavoriteFriend()
            if greet.can_start(self, world):
                candidates.append(greet)

        if not candidates:
            self.goal = None
            return

        # Priority: sequence first, then food, then greet
        self.goal = candidates[0]
        self.goal.start(now=world.tick)
        world._last_goal = f"{self.name} selects goal: {self.goal.name}"

        # avoid flapping
        self._goal_cooldown = 2

    def act_on_goal(self, world) -> bool:
        """Execute one step toward the current goal if any. Returns True if acted."""
        if not self.goal or self.goal.done():
            return False
        acted = self.goal.step(self, world)
        if self.goal.done():
            self._goal_cooldown = 2
        return acted

    # ---- Turn logic -------------------------------------------------------
    def tick(self, world):
        # Memory decays every tick
        self.memory.decay()
        self._recent_event = None

        # Passive energy drain
        self.energy -= 1

        # If out of energy, nap
        if self.energy <= 0:
            self.energy = 6  # nap restores energy
            self.mood = max(-5, self.mood - 1)
            world.grid.place(self.x, self.y, self)  # stay put
            self._recent_event = "nap"
            world._last_log = f"{self.name} takes a nap."
            world._last_mood = self.mood
            self._update_emotion(world)
            return

        # Try goals first (including chain)
        self.consider_goals(world)
        if self.act_on_goal(world):
            self._update_emotion(world)
            return

        # Fallback behaviors -------------------------------------------------

        # If hungry and we remember food, head toward it
        if self.energy <= 6 and self.memory.last_food:
            step = self.choose_step_towards(world, self.memory.last_food)
            if step:
                nx, ny = step
                world.grid.move(self.x, self.y, nx, ny)
                self.x, self.y = nx, ny
                self.mood = min(5, self.mood + 0.2)
                world._last_log = (
                    f"{self.name} heads toward remembered food at "
                    f"{self.memory.last_food}."
                )
                world._last_mood = self.mood
                self._update_emotion(world)
                return

        # Eat if food is adjacent (also update memory)
        food_loc = self.find_adjacent_food(world)
        if food_loc:
            fx, fy = food_loc
            world.grid.move(self.x, self.y, fx, fy)
            self.x, self.y = fx, fy
            self.energy = min(15, self.energy + 5)
            self.mood = min(5, self.mood + 1.5)
            self.memory.remember_food(fx, fy)
            self._recent_event = "eat"
            world._last_log = (
                f"{self.name} munches on food at ({fx},{fy}) and remembers this spot."
            )
            world._last_mood = self.mood
            self._update_emotion(world)
            return

        # Social baseline
        friend_loc = self.find_adjacent_friend(world)
        if friend_loc:
            fx, fy = friend_loc
            friend = world.grid.get(fx, fy)
            if friend is not None and isinstance(friend, Simulite):
                affinity = self.memory.get_affinity(friend.name)
                if affinity <= -1.0:
                    step = self.choose_step_away_from(world, (fx, fy))
                    if step:
                        nx, ny = step
                        world.grid.move(self.x, self.y, nx, ny)
                        self.x, self.y = nx, ny
                        self.mood = max(-5, self.mood - 0.1)
                        world._last_log = (
                            f"{self.name} avoids {friend.name} "
                            f"(affinity {affinity:+.1f})."
                        )
                        world._last_mood = self.mood
                        self._update_emotion(world)
                        return
                if self.traits.sociability >= 6:
                    if self.mood >= 0:
                        self.mood = min(5, self.mood + 0.5)
                        friend.mood = min(5, friend.mood + 0.4)
                        self.memory.update_affinity(friend.name, +0.4)
                        quip = random.choice(POSITIVE_QUIPS)
                        self._recent_event = "social_pos"
                        world._last_log = (
                            f"{self.name} to {friend.name}: “{quip}” "
                            f"(affinity {self.memory.get_affinity(friend.name):+.1f})"
                        )
                    else:
                        self.mood = max(-5, self.mood + 0.2)
                        friend.mood = max(-5, friend.mood - 0.2)
                        self.memory.update_affinity(friend.name, -0.3)
                        quip = random.choice(NEGATIVE_QUIPS)
                        self._recent_event = "social_neg"
                        world._last_log = (
                            f"{self.name} to {friend.name}: “{quip}” "
                            f"(affinity {self.memory.get_affinity(friend.name):+.1f})"
                        )
                    world._last_mood = self.mood
                    self._update_emotion(world)
                    return

        # Otherwise wander
        attempts = 1 + (self.traits.curiosity // 4)
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

        self.mood = max(-5, self.mood - 0.5)
        world._last_log = f"{self.name} feels stuck."
        world._last_mood = self.mood
        self._recent_event = "blocked"
        self._update_emotion(world)

    def _update_emotion(self, world):
        self.emotion = compute_emotion(self.energy, self.mood, self._recent_event)
        world._last_emotion = str(self.emotion)
