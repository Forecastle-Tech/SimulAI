from __future__ import annotations
import json
from typing import Any, Dict, List, Optional, Tuple, Union
import os

# Optional YAML support
try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - YAML is optional
    yaml = None

from simulai.environment.grid import Grid
from simulai.environment.resources import Food
from simulai.environment.events import Weather
from simulai.core.world import World
from simulai.agents.simulite import Simulite
from simulai.agents.traits import Traits
from simulai.agents.memory import Memory
from simulai.agents.goals import (
    Goal, GoalStatus,
    VisitRememberedFood, GreetFavoriteFriend,
    SequenceGoal
)

_VERSION = "0.1.0"

# -------------------- Helpers --------------------

def _enum_to_str(status: GoalStatus) -> str:
    return status.name

def _enum_from_str(name: str) -> GoalStatus:
    return GoalStatus[name]

def _tuple_or_none(v: Optional[Tuple[int,int]]) -> Optional[List[int]]:
    return list(v) if v is not None else None

def _tuple_from_list(v: Optional[List[int]]) -> Optional[Tuple[int,int]]:
    if v is None:
        return None
    return (int(v[0]), int(v[1]))

# -------------------- Goal <-> dict --------------------

def goal_to_dict(goal: Optional[Goal]) -> Optional[Dict[str, Any]]:
    if goal is None:
        return None

    base: Dict[str, Any] = {
        "kind": goal.__class__.__name__,
        "name": getattr(goal, "name", goal.__class__.__name__),
        "status": _enum_to_str(getattr(goal, "status", GoalStatus.PENDING)),
        "started_at": getattr(goal, "started_at", None),
        "reason": getattr(goal, "reason", ""),
    }

    if isinstance(goal, VisitRememberedFood):
        base["state"] = {
            "target": _tuple_or_none(getattr(goal, "target", None)),
        }
        return base

    if isinstance(goal, GreetFavoriteFriend):
        base["state"] = {
            "target_name": getattr(goal, "target_name", None),
            "threshold": getattr(goal, "threshold", 0.8),
        }
        return base

    if isinstance(goal, SequenceGoal):
        children = [goal_to_dict(ch) for ch in goal.children]
        base["state"] = {
            "index": getattr(goal, "index", 0),
            "children": children,
        }
        return base

    # Unknown goal type: store minimal info
    base["state"] = {}
    return base


def goal_from_dict(d: Optional[Dict[str, Any]]) -> Optional[Goal]:
    if d is None:
        return None
    kind = d.get("kind")
    name = d.get("name", kind)
    status = _enum_from_str(d.get("status", "PENDING"))
    started_at = d.get("started_at")
    reason = d.get("reason", "")
    state = d.get("state", {}) or {}

    def _apply_common(g: Goal) -> Goal:
        g.name = name or g.name
        g.status = status
        g.started_at = started_at
        g.reason = reason
        return g

    if kind == "VisitRememberedFood":
        g = _apply_common(VisitRememberedFood())
        g.target = _tuple_from_list(state.get("target"))
        return g

    if kind == "GreetFavoriteFriend":
        g = _apply_common(GreetFavoriteFriend())
        g.target_name = state.get("target_name")
        th = state.get("threshold")
        if isinstance(th, (int, float)):
            g.threshold = float(th)
        return g

    if kind == "SequenceGoal" or kind == "Sequence":
        g = _apply_common(SequenceGoal())
        g.index = int(state.get("index", 0))
        children_raw = state.get("children", []) or []
        g.children = [goal_from_dict(cr) for cr in children_raw if cr is not None]  # type: ignore
        return g

    # Unknown -> bare Goal
    g = _apply_common(Goal(name=name or "Goal"))
    return g

# -------------------- Agent <-> dict --------------------

def simulite_to_dict(s: Simulite) -> Dict[str, Any]:
    return {
        "type": "Simulite",
        "name": s.name,
        "pos": {"x": s.x, "y": s.y},
        "energy": s.energy,
        "mood": s.mood,
        "traits": {
            "curiosity": s.traits.curiosity,
            "sociability": s.traits.sociability,
        },
        "memory": {
            "last_food": _tuple_or_none(s.memory.last_food),
            "friend_affinity": dict(s.memory.friend_affinity),
        },
        "goal": goal_to_dict(getattr(s, "goal", None)),
    }

def simulite_from_dict(d: Dict[str, Any]) -> Simulite:
    name = d["name"]
    pos = d.get("pos", {})
    x = int(pos.get("x", 0))
    y = int(pos.get("y", 0))
    traits_d = d.get("traits", {})
    traits = Traits(
        curiosity=int(traits_d.get("curiosity", 5)),
        sociability=int(traits_d.get("sociability", 5)),
    )
    s = Simulite(name=name, x=x, y=y, traits=traits)
    s.energy = int(d.get("energy", s.energy))
    s.mood = float(d.get("mood", s.mood))

    mem = d.get("memory", {}) or {}
    s.memory.last_food = _tuple_from_list(mem.get("last_food"))
    fa = mem.get("friend_affinity", {}) or {}
    s.memory.friend_affinity = {str(k): float(v) for k, v in fa.items()}

    s.goal = goal_from_dict(d.get("goal"))
    return s

# -------------------- World <-> dict --------------------

def world_to_dict(world: World) -> Dict[str, Any]:
    width = world.grid.width
    height = world.grid.height

    # resources: scan grid for Food
    resources: List[Dict[str, Any]] = []
    for y in range(height):
        for x in range(width):
            cell = world.grid.get(x, y)
            if isinstance(cell, Food):
                resources.append({"type": "Food", "x": x, "y": y, "energy": cell.energy})

    agents = []
    for a in world.agents:
        if isinstance(a, Simulite):
            agents.append(simulite_to_dict(a))
        # else: ignore unknown types for now

    return {
        "version": _VERSION,
        "world": {
            "width": width,
            "height": height,
            "tick": world.tick,
            "weather": {"kind": world.weather.kind, "duration": world.weather.duration},
            "resources": resources,
            "agents": agents,
        }
    }

def world_from_dict(data: Dict[str, Any]) -> World:
    wd = data.get("world", {})
    width = int(wd.get("width", 8))
    height = int(wd.get("height", 8))
    tick = int(wd.get("tick", 0))
    weather_d = wd.get("weather", {}) or {"kind": "clear", "duration": 5}

    grid = Grid(width=width, height=height)
    # Create a temp world to attach weather/tick after init
    world = World(grid=grid)
    world.tick = tick
    world.weather = Weather(kind=str(weather_d.get("kind", "clear")),
                            duration=int(weather_d.get("duration", 5)))

    # Place resources
    for r in wd.get("resources", []) or []:
        if r.get("type") == "Food":
            x = int(r.get("x", 0))
            y = int(r.get("y", 0))
            energy = int(r.get("energy", 5))
            grid.place(x, y, Food(energy=energy))

    # Place agents
    for ad in wd.get("agents", []) or []:
        if ad.get("type") == "Simulite":
            s = simulite_from_dict(ad)
            world.add_agent(s)
        # unknown types ignored

    return world

# -------------------- File I/O --------------------

def _infer_format(path: str, fmt: Optional[str]) -> str:
    if fmt:
        return fmt.lower()
    ext = os.path.splitext(path)[1].lower()
    if ext in (".yaml", ".yml"):
        return "yaml"
    return "json"

def save_world(path: str, world: World, fmt: Optional[str] = None) -> None:
    fmt_ = _infer_format(path, fmt)
    data = world_to_dict(world)
    if fmt_ == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return
    if fmt_ == "yaml":
        if yaml is None:
            raise RuntimeError("YAML requested but PyYAML is not installed. Run: pip install pyyaml")
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)
        return
    raise ValueError(f"Unknown format: {fmt_}")

def load_world(path: str) -> World:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".yaml", ".yml"):
        if yaml is None:
            raise RuntimeError("Cannot load YAML; PyYAML not installed. Run: pip install pyyaml")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    else:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    return world_from_dict(data)
