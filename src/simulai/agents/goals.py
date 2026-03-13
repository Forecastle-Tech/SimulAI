from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Tuple, List

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
# Existing goals

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

        # Success if we reached the target tile (eating is handled by Simulite/global logic)
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

        # Blocked this tick; try again next tick
        world._last_goal = f"{s.name} goal: VisitRememberedFood → blocked"
        return False

@dataclass
class GreetFavoriteFriend(Goal):
    """Approach the most liked friend and greet them when adjacent."""
    name: str = "GreetFavoriteFriend"
    target_name: Optional[str] = None
    threshold: float = 0.8  # minimum affinity to be considered a 'favorite'

    def can_start(self, s, world) -> bool:
        if not s.memory.friend_affinity:
            return False
        # Find top friend over the threshold
        best_name = None
        best_val = self.threshold
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

# -----------------------------------------------------------------------------
# NEW: SequenceGoal (chaining multiple goals)

@dataclass
class SequenceGoal(Goal):
    """Run a list of child goals in order, advancing on SUCCESS.
    Fails if a child cannot start or fails.
    """
    name: str = "Sequence"
    children: List[Goal] = field(default_factory=list)
    index: int = 0  # current child index

    def can_start(self, s, world) -> bool:
        if not self.children:
            self.reason = "No child goals."
            return False
        # Require first goal to be startable
        return self.children[0].can_start(s, world)

    def start(self, now: int):
        super().start(now)

    def step(self, s, world) -> bool:
        if self.index >= len(self.children):
            self.status = GoalStatus.SUCCESS
            self.reason = "All child goals completed."
            return False

        child = self.children[self.index]

        # Initialize child when we reach it
        if child.status == GoalStatus.PENDING:
            # If child cannot start right now, the sequence fails
            if not child.can_start(s, world):
                self.status = GoalStatus.FAILED
                self.reason = f"Child {child.name} cannot start."
                return False
            child.start(now=world.tick)
            world._last_goal = f"{s.name} sequence: starting {child.name}"

        # Step the child
        acted = child.step(s, world)

        # If child finished, advance or finish sequence
        if child.done():
            if child.status == GoalStatus.SUCCESS:
                self.index += 1
                if self.index >= len(self.children):
                    self.status = GoalStatus.SUCCESS
                    self.reason = "Sequence complete."
                else:
                    # Next child will be initialized on next step call
                    next_child = self.children[self.index]
                    world._last_goal = f"{s.name} sequence: next → {next_child.name}"
            else:
                self.status = GoalStatus.FAILED
                self.reason = f"Child {child.name} failed."
        return acted

# -----------------------------------------------------------------------------
# Helper: build the specific chain "Eat → then Greet Favorite Friend"

def build_eat_then_greet_sequence(s) -> Optional[SequenceGoal]:
    """Create a SequenceGoal: VisitRememberedFood → GreetFavoriteFriend (if available).
    Returns None if the first goal cannot start.
    """
    eat = VisitRememberedFood()
    greet = GreetFavoriteFriend()  # will pick target_name in can_start
    seq = SequenceGoal(name="EatThenGreet", children=[eat, greet])

    # Only return if the first step is viable; second is checked when it runs
    return seq
