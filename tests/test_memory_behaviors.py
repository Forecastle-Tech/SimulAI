from simulai.agents.simulite import Simulite
from simulai.agents.traits import Traits
from simulai.core.world import World
from simulai.environment.grid import Grid
from simulai.environment.resources import Food


def test_moves_toward_remembered_food_when_hungry():
    grid = Grid(8, 5)
    w = World(grid)
    s = Simulite("A", 2, 2, traits=Traits(curiosity=1, sociability=1))
    w.add_agent(s)
    # Place remembered food ahead; don't actually place Food there; we only test movement bias
    s.memory.remember_food(5, 2)
    s.energy = 5  # hungry threshold <= 6
    old_dist = abs(s.x - 5) + abs(s.y - 2)
    w.step()
    new_dist = abs(s.x - 5) + abs(s.y - 2)
    assert new_dist <= old_dist, "Should not move away from target when hungry."


def test_eating_updates_last_food_memory():
    grid = Grid(6, 6)
    w = World(grid)
    s = Simulite("A", 2, 2, traits=Traits(curiosity=1, sociability=1))
    w.add_agent(s)
    grid.place(3, 2, Food(energy=5))
    w.step()  # should move into (3,2) and eat
    assert s.memory.last_food == (3, 2)


def test_affinity_updates_on_interaction():
    grid = Grid(6, 6)
    w = World(grid)
    a = Simulite("A", 2, 2, traits=Traits(curiosity=1, sociability=8))
    b = Simulite("B", 3, 2, traits=Traits(curiosity=1, sociability=8))
    w.add_agent(a)
    w.add_agent(b)
    before = a.memory.get_affinity("B")
    # Make A positive mood to favor positive interaction
    a.mood = 1.0
    w.step()
    after = a.memory.get_affinity("B")
    assert after != before


def test_avoid_disliked_friend():
    grid = Grid(6, 6)
    w = World(grid)
    a = Simulite("A", 2, 2, traits=Traits(curiosity=1, sociability=8))
    b = Simulite("B", 3, 2, traits=Traits(curiosity=1, sociability=8))
    w.add_agent(a)
    w.add_agent(b)
    # Seed negative affinity
    a.memory.update_affinity("B", -2.0)
    # Make sure there's space to move away (to the left)
    # Step should try to increase distance from B at (3,2)
    prev_dist = abs(a.x - b.x) + abs(a.y - b.y)
    w.step()
    new_dist = abs(a.x - b.x) + abs(a.y - b.y)
    assert new_dist >= prev_dist, "Should not move closer to a disliked friend."
