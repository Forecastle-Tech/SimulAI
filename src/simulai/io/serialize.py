from __future__ import annotations

import json
from pathlib import Path

from simulai.agents.simulite import Goal, Simulite
from simulai.agents.traits import Traits
from simulai.core.world import World
from simulai.environment.grid import Grid
from simulai.environment.resources import Food

try:
    import yaml
except ImportError:
    yaml = None


def _agent_to_dict(agent: Simulite) -> dict:
    return {
        "name": agent.name,
        "x": agent.x,
        "y": agent.y,
        "alive": agent.alive,
        "cause_of_death": agent.cause_of_death,
        "generation": agent.generation,
        "age_ticks": agent.age_ticks,
        "max_age_ticks": agent.max_age_ticks,
        "life_stage": agent.life_stage,
        "life_force": agent.life_force,
        "health": agent.health,
        "energy": agent.energy,
        "nutrition": agent.nutrition,
        "rest": agent.rest,
        "exercise": agent.exercise,
        "social": agent.social,
        "contribution": agent.contribution,
        "morality": agent.morality,
        "risk_load": agent.risk_load,
        "reproduction_load": agent.reproduction_load,
        "speed": agent.speed,
        "agility": agent.agility,
        "births": agent.births,
        "generation_depth": agent.generation_depth,
        "last_action": agent.last_action,
        "move_mode": agent.move_mode,
        "target_zone": agent.target_zone,
        "target_chip": agent.target_chip,
        "mood": agent.mood,
        "emotion": agent.emotion,
        "goal": {
            "name": agent.goal.name,
            "payload": list(agent.goal.payload)
            if isinstance(agent.goal.payload, tuple)
            else agent.goal.payload,
            "stage": agent.goal.stage,
        }
        if agent.goal is not None
        else None,
        "traits": {
            "curiosity": agent.traits.curiosity,
            "sociability": agent.traits.sociability,
            "discipline": agent.traits.discipline,
            "resilience": agent.traits.resilience,
            "metabolism": agent.traits.metabolism,
            "kindness": agent.traits.kindness,
            "caution": agent.traits.caution,
        },
        "memory": {
            "last_food": list(agent.memory.last_food) if agent.memory.last_food else None,
            "affinity": dict(agent.memory.affinity),
            "friend_affinity": dict(agent.memory.friend_affinity),
        },
        "action_memory": dict(agent.action_memory),
        "action_counts": dict(agent.action_counts),
        "zone_memory": dict(agent.zone_memory),
        "zone_visit_counts": dict(agent.zone_visit_counts),
        "chip_memory": dict(agent.chip_memory),
        "reproduction_boost": agent.reproduction_boost,
    }


def _agent_from_dict(data: dict) -> Simulite:
    traits_data = data.get("traits", {})
    traits = Traits(
        curiosity=traits_data.get("curiosity", 5.0),
        sociability=traits_data.get("sociability", 5.0),
        discipline=traits_data.get("discipline", 5.0),
        resilience=traits_data.get("resilience", 5.0),
        metabolism=traits_data.get("metabolism", 5.0),
        kindness=traits_data.get("kindness", 5.0),
        caution=traits_data.get("caution", 5.0),
    )

    agent = Simulite(
        name=data["name"],
        x=data["x"],
        y=data["y"],
        traits=traits,
        alive=data.get("alive", True),
        cause_of_death=data.get("cause_of_death"),
        generation=data.get("generation", 1),
        age_ticks=data.get("age_ticks", 0),
        max_age_ticks=data.get("max_age_ticks", 220),
        life_stage=data.get("life_stage", "juvenile"),
        life_force=data.get("life_force", 50.0),
        health=data.get("health", 50.0),
        energy=data.get("energy", 50.0),
        nutrition=data.get("nutrition", 50.0),
        rest=data.get("rest", 50.0),
        exercise=data.get("exercise", 30.0),
        social=data.get("social", 40.0),
        contribution=data.get("contribution", 20.0),
        morality=data.get("morality", 50.0),
        risk_load=data.get("risk_load", 10.0),
        reproduction_load=data.get("reproduction_load", 0.0),
        speed=data.get("speed", 0.6),
        agility=data.get("agility", 0.6),
        births=data.get("births", 0),
        generation_depth=data.get("generation_depth", data.get("generation", 1)),
        last_action=data.get("last_action", "idle"),
        move_mode=data.get("move_mode", "wander"),
        target_zone=data.get("target_zone"),
        target_chip=data.get("target_chip"),
        mood=data.get("mood", 50.0),
        emotion=data.get("emotion", "neutral"),
        reproduction_boost=data.get("reproduction_boost", 0.0),
    )

    memory_data = data.get("memory", {})
    last_food = memory_data.get("last_food")
    if isinstance(last_food, (list, tuple)) and len(last_food) == 2:
        agent.memory.last_food = (int(last_food[0]), int(last_food[1]))
    else:
        agent.memory.last_food = None

    affinity = memory_data.get("affinity")
    if affinity is None:
        affinity = memory_data.get("friend_affinity", {})
    agent.memory.affinity = dict(affinity)

    goal_data = data.get("goal")
    if isinstance(goal_data, dict):
        goal_payload = goal_data.get("payload")
        if isinstance(goal_payload, list) and len(goal_payload) == 2:
            goal_payload = (int(goal_payload[0]), int(goal_payload[1]))
        agent.goal = Goal(
            name=goal_data.get("name", "UnknownGoal"),
            payload=goal_payload,
            stage=goal_data.get("stage", "start"),
        )
    else:
        agent.goal = None

    agent.action_memory.update(data.get("action_memory", {}))
    agent.action_counts.update(data.get("action_counts", {}))
    agent.zone_memory.update(data.get("zone_memory", {}))
    agent.zone_visit_counts.update(data.get("zone_visit_counts", {}))
    agent.chip_memory.update(data.get("chip_memory", {}))

    agent.clamp_state()
    return agent


def world_to_dict(world: World) -> dict:
    foods: list[dict] = []

    for y in range(world.grid.height):
        for x in range(world.grid.width):
            obj = world.grid.get(x, y)
            if isinstance(obj, Food):
                foods.append(
                    {
                        "x": x,
                        "y": y,
                        "energy": getattr(obj, "energy", 5),
                    }
                )

    for x, y in sorted(world.food):
        if not any(f["x"] == x and f["y"] == y for f in foods):
            foods.append({"x": x, "y": y, "energy": 5})

    return {
        "width": world.grid.width,
        "height": world.grid.height,
        "tick": getattr(world, "tick", getattr(world, "tick_count", 0)),
        "tick_count": getattr(world, "tick_count", getattr(world, "tick", 0)),
        "next_child_id": getattr(world, "next_child_id", 1),
        "max_population": getattr(world, "max_population", 24),
        "max_generation_limit": getattr(world, "max_generation_limit", 6),
        "weather": {
            "state": getattr(getattr(world, "weather", None), "state", "clear"),
            "duration": getattr(getattr(world, "weather", None), "duration", 5),
            "progress": getattr(getattr(world, "weather", None), "progress", 0),
        },
        "chips": [
            {"x": x, "y": y, "type": chip_type} for (x, y), chip_type in sorted(world.chips.items())
        ],
        "agents": [_agent_to_dict(agent) for agent in world.agents],
        "foods": foods,
        "deaths_by_cause": dict(getattr(world, "deaths_by_cause", {})),
        "metrics_history": list(getattr(world, "metrics_history", [])),
    }


def world_from_dict(data: dict) -> World:
    grid = Grid(data["width"], data["height"])
    world = World(grid)

    world.tick = data.get("tick", data.get("tick_count", 0))
    world.tick_count = data.get("tick_count", data.get("tick", 0))
    world.next_child_id = data.get("next_child_id", 1)
    world.max_population = data.get("max_population", 24)
    world.max_generation_limit = data.get("max_generation_limit", 6)
    world.deaths_by_cause = dict(data.get("deaths_by_cause", {}))
    world.metrics_history = list(data.get("metrics_history", []))

    weather_data = data.get("weather", {})
    if hasattr(world, "weather"):
        world.weather.state = weather_data.get("state", "clear")
        world.weather.duration = weather_data.get("duration", 5)
        world.weather.progress = weather_data.get("progress", 0)

    for item in data.get("foods", []):
        x = item["x"]
        y = item["y"]
        energy = item.get("energy", 5)
        world.food.add((x, y))
        try:
            grid.place(x, y, Food(energy=energy))
        except Exception:
            pass

    for item in data.get("chips", []):
        world.chips[(item["x"], item["y"])] = item["type"]

    for item in data.get("agents", []):
        agent = _agent_from_dict(item)
        world.add_agent(agent)

    return world


def save_world(path: str | Path, world: World, fmt: str | None = None) -> None:
    path = Path(path)
    data = world_to_dict(world)

    out_fmt = fmt.lower() if fmt else path.suffix.lower().lstrip(".")
    if out_fmt == "":
        out_fmt = "json"

    if out_fmt in {"yaml", "yml"}:
        if yaml is None:
            raise RuntimeError("Cannot save YAML; PyYAML not installed. Run: pip install pyyaml")
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)
    else:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def load_world(path: str | Path) -> World:
    path = Path(path)
    in_fmt = path.suffix.lower().lstrip(".")

    if in_fmt in {"yaml", "yml"}:
        if yaml is None:
            raise RuntimeError("Cannot load YAML; PyYAML not installed. Run: pip install pyyaml")
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    else:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

    return world_from_dict(data)
