import json
import os
import tempfile

from simulai.core.world import World
from simulai.environment.grid import Grid
from simulai.agents.simulite import Simulite
from simulai.agents.traits import Traits
from simulai.environment.resources import Food
from simulai.io.serialize import world_to_dict, world_from_dict, save_world, load_world

def build_small_world():
    grid = Grid(6, 5)
    w = World(grid)
    a = Simulite("A", 1, 1, traits=Traits(curiosity=3, sociability=7))
    b = Simulite("B", 4, 3, traits=Traits(curiosity=6, sociability=5))
    w.add_agent(a)
    w.add_agent(b)
    w.sprinkle_food(count=2)
    # seed memory & affinity
    a.memory.last_food = (2, 1)
    a.memory.friend_affinity = {"B": 1.4}
    return w, a, b

def test_world_to_from_dict_roundtrip():
    w, a, b = build_small_world()
    w.step()
    data = world_to_dict(w)
    w2 = world_from_dict(data)

    assert w2.grid.width == w.grid.width
    assert w2.grid.height == w.grid.height
    assert len(w2.agents) == len(w.agents)

    names = sorted([ag.name for ag in w2.agents])
    assert "A" in names and "B" in names

    a2 = next(ag for ag in w2.agents if ag.name == "A")
    assert a2.memory.last_food == (2, 1)
    assert a2.memory.friend_affinity.get("B", 0) > 1.3

def test_save_load_json_tmpfile():
    w, a, b = build_small_world()
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "world.json")
        save_world(path, w, fmt="json")
        w2 = load_world(path)
        assert len(w2.agents) == 2
        a2 = next(ag for ag in w2.agents if ag.name == "A")
        assert a2.name == "A"
