from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from simulai.agents.simulite import Simulite


class GoalStatus(Enum):
    PENDING = auto()
    ACTIVE = auto()
    SUCCEEDED = auto()
    FAILED = auto()


@dataclass
class Goal:
    name: str
    status: GoalStatus = GoalStatus.PENDING
    started_at: Optional[int] = None
    completed_at: Optional[int] = None

    def start(self, now: int) -> None:
        if self.status == GoalStatus.PENDING:
            self.status = GoalStatus.ACTIVE
            self.started_at = now

    def succeed(self, now: int) -> None:
        self.status = GoalStatus.SUCCEEDED
        self.completed_at = now

    def fail(self, now: int) -> None:
        self.status = GoalStatus.FAILED
        self.completed_at = now

    def done(self) -> bool:
        return self.status in {GoalStatus.SUCCEEDED, GoalStatus.FAILED}

    def can_start(self, agent: "Simulite", world) -> bool:
        return True

    def step(self, agent: "Simulite", world) -> bool:
        raise NotImplementedError


@dataclass
class VisitRememberedFood(Goal):
    name: str = "VisitRememberedFood"

    def can_start(self, agent: "Simulite", world) -> bool:
        return agent.memory.last_food is not None

    def step(self, agent: "Simulite", world) -> bool:
        target = agent.memory.last_food
        if target is None:
            self.fail(world.tick)
            return False

        if (agent.x, agent.y) == target:
            self.succeed(world.tick)
            return False

        step = agent.choose_step_towards(world, target)
        if step is None:
            self.fail(world.tick)
            return False

        nx, ny = step
        world.grid.move(agent.x, agent.y, nx, ny)
        agent.x, agent.y = nx, ny
        world._last_log = f"{agent.name} moves toward remembered food at {target}."
        world._last_mood = agent.mood
        return True


@dataclass
class GreetFavoriteFriend(Goal):
    name: str = "GreetFavoriteFriend"
    target_name: Optional[str] = None

    def can_start(self, agent: "Simulite", world) -> bool:
        self.target_name = agent._favorite_friend_name()
        return self.target_name is not None

    def step(self, agent: "Simulite", world) -> bool:
        if not self.target_name:
            self.fail(world.tick)
            return False

        target = None
        for other in getattr(world, "agents", []):
            if other is not agent and other.name == self.target_name:
                target = other
                break

        if target is None:
            self.fail(world.tick)
            return False

        if abs(agent.x - target.x) + abs(agent.y - target.y) == 1:
            agent.memory.update_affinity(target.name, 0.2)
            world._last_log = f"{agent.name} greets favorite friend {target.name}."
            world._last_mood = agent.mood
            self.succeed(world.tick)
            return True

        step = agent.choose_step_towards(world, (target.x, target.y))
        if step is None:
            self.fail(world.tick)
            return False

        nx, ny = step
        world.grid.move(agent.x, agent.y, nx, ny)
        agent.x, agent.y = nx, ny
        world._last_log = f"{agent.name} heads toward friend {target.name}."
        world._last_mood = agent.mood
        return True


@dataclass
class SequenceGoal(Goal):
    children: List[Goal] = field(default_factory=list)
    current_index: int = 0
    name: str = "SequenceGoal"

    def can_start(self, agent: "Simulite", world) -> bool:
        return bool(self.children) and self.children[0].can_start(agent, world)

    def step(self, agent: "Simulite", world) -> bool:
        if self.current_index >= len(self.children):
            self.succeed(world.tick)
            return False

        current = self.children[self.current_index]

        if current.status == GoalStatus.PENDING:
            if not current.can_start(agent, world):
                self.fail(world.tick)
                return False
            current.start(world.tick)

        acted = current.step(agent, world)

        if current.status == GoalStatus.SUCCEEDED:
            self.current_index += 1
            if self.current_index >= len(self.children):
                self.succeed(world.tick)
        elif current.status == GoalStatus.FAILED:
            self.fail(world.tick)

        return acted


def build_eat_then_greet_sequence(agent: "Simulite") -> Optional[SequenceGoal]:
    """
    Build a sequence goal: visit remembered food, then greet favorite friend.
    """
    eat = VisitRememberedFood()
    greet = GreetFavoriteFriend()
    seq = SequenceGoal(name="EatThenGreet", children=[eat, greet])

    return seq
