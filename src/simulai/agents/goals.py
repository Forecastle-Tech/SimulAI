from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Tuple

class GoalStatus(Enum):
    PENDING = auto()
    ACTIVE = auto()
    SUCCESS = auto()
    FAILED = auto()

@dataclass
class Goal:
    name: str
    status: GoalStatus = GoalStatus.PENDING
    started_at: Optional[int] = None
    reason: str = ""

    def can_start(self, s, world) -> bool:
        return True

    def start(self, now: int):
        self.status = GoalStatus.ACTIVE
        self.started_at = now

    def step(self, s, world) -> bool:
        """Return True if an action was taken this tick."""
        raise NotImplementedError

    def done(self) -> bool:
        return self.status in (GoalStatus.SUCCESS, GoalStatus.FAILED)

# -----------------------------------------------------------------------------

@dataclass
class VisitRememberedFood(Goal):
    """Move toward last remembered food location (if hungry)."""
    name: str = "VisitRememberedFood"
    target: Optional[Tuple[int, int]] = None

    def can_start(self, s, world) -> bool:
        return s.memory.last_food is not None and s.energy <= 7

    def start(self, now: int):
        super().start(now)

    def step(self, s, world) -> bool:
        if self.target is None:
            self.target = s.memory.last_food
        if self.target is None:
            self.status = GoalStatus.FAILED
            self.reason = "No remembered food."
            return False

        # If we already reached the target, we're successful (eating is handled by Simulite logic)
        if (s.x, s.y) == self.target:
            self.status = GoalStatus.SUCCESS
            self.reason = "Reached remembered food."
            return False

        # Move one step toward the target if possible
        step = s.choose_step_towards(world, self.target)
        if step:
            nx, ny = step
            world.grid.move(s.x, s.y, nx, ny)
            s.x, s.y = nx, ny
            s.mood = min(5, s.mood + 0.2)
            world._last_log = f"{s.name} pursues goal → heading to food at {self.target}."
            world._last_mood = s.mood
            world._last_goal = f"{s.name} goal: VisitRememberedFood → moving toward {self.target}"
            return True

        # If we can't move closer this tick, keep goal ACTIVE and try again next tick
        world._last_goal = f"{s.name} goal: VisitRememberedFood → blocked"
        return False

# -----------------------------------------------------------------------------

@dataclass
class GreetFavoriteFriend(Goal):
    """Approach the most liked friend and greet them when adjacent."""
    name: str = "GreetFavoriteFriend"
    target_name: Optional[str] = None

    def can_start(self, s, world) -> bool:
        # Pick friend with highest positive affinity
        if not s.memory.friend_affinity:
            return False
        best_name = None
        best_val = 0.8  # threshold for "favorite"
        for k, v in s.memory.friend_affinity.items():
            if v > best_val:
                best_val = v
                best_name = k
        if best_name is None:
            return False
        self.target_name = best_name
        return True

    def step(self, s, world) -> bool:
        if not self.target_name:
            self.status = GoalStatus.FAILED
            self.reason = "No target friend."
            return False

        # Find target agent by name
        target = None
        for agent in world.agents:
            if getattr(agent, "name", None) == self.target_name:
                target = agent
                break

        if target is None:
            self.status = GoalStatus.FAILED
            self.reason = f"{self.target_name} not found."
            return False

        # If adjacent, greet and succeed
        manhattan = abs(s.x - target.x) + abs(s.y - target.y)
        if manhattan == 1:
            # Positive interaction
            s.mood = min(5, s.mood + 0.5)
            target.mood = min(5, getattr(target, "mood", 0) + 0.4)
            s.memory.update_affinity(self.target_name, +0.2)
            world._last_log = f"{s.name} greets {self.target_name} warmly. 🤝"
            world._last_mood = s.mood
            world._last_goal = f"{s.name} goal: GreetFavoriteFriend → greeted {self.target_name}"
            self.status = GoalStatus.SUCCESS
            self.reason = "Greeted favorite friend."
            return True

        # Otherwise, move toward friend if possible
        step = s.choose_step_towards(world, (target.x, target.y))
        if step:
            nx, ny = step
            world.grid.move(s.x, s.y, nx, ny)
            s.x, s.y = nx, ny
            world._last_log = f"{s.name} pursues goal → approaching {self.target_name}."
            world._last_mood = s.mood
            world._last_goal = f"{s.name} goal: GreetFavoriteFriend → moving toward {self.target_name}"
            return True

        world._last_goal = f"{s.name} goal: GreetFavoriteFriend → blocked en route to {self.target_name}"
        return False
``
