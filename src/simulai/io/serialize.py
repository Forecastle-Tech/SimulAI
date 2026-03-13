from __future__ import annotations

import json
from pathlib import Path

from simulai.agents.simulite import Simulite
from simulai.core.world import World
from simulai.environment.grid import Grid
from simulai.environment.resources import Food

try:
    import yaml
except ImportError:
    yaml = None


def world_to_dict(world: World) -> dict:
    agents = []
    foods = []

    for y in range(world.grid.height):
        for x in range(world.grid.width):
            obj = world.grid.get(x, y)
            if isinstance(obj, Simulite):
                agents.append(
                    {
                        "name": obj.name,
                        "x": obj.x,
                        "y": obj.y,
                        "energy": obj.energy,
                        "mood": obj.mood,
                    }
                )
            elif isinstance(obj, Food):
                foods.append({"x": x, "y": y})

    return {
        "width": world.grid.width,
        "height": world.grid.height,
        "tick": getattr(world, "tick", 0),
        "agents": agents,
        "foods": foods,
    }


def world_from_dict(data: dict) -> World:
    grid = Grid(data["width"], data["height"])
    world = World(grid)
    world.tick = data.get("tick", 0)

    for item in data.get("foods", []):
        grid.place(item["x"], item["y"], Food())

    for item in data.get("agents", []):
        agent = Simulite(item["name"], item["x"], item["y"])
        agent.energy = item.get("energy", agent.energy)
        agent.mood = item.get("mood", agent.mood)
        world.add_agent(agent)

    return world


def save_world(world: World, path: str | Path) -> None:
    path = Path(path)
    data = world_to_dict(world)

    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("Cannot save YAML; PyYAML not installed. Run: pip install pyyaml")
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def load_world(path: str | Path) -> World:
    path = Path(path)

    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("Cannot load YAML; PyYAML not installed. Run: pip install pyyaml")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    else:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    return world_from_dict(data)
