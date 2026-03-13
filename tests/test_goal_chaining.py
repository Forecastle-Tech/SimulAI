from simulai.agents.simulite import Simulite
from simulai.agents.traits import Traits
from simulai.core.world import World
from simulai.environment.grid import Grid


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def test_chain_selected_when_hungry_and_food_remembered():
    grid = Grid(10, 5)
    w = World(grid)
    a = Simulite("A", 2, 2, traits=Traits(curiosity=1, sociability=8))
    b = Simulite("B", 7, 2, traits=Traits(curiosity=1, sociability=8))
    w.add_agent(a)
    w.add_agent(b)

    # conditions: hungry + remembered food + favorite friend present
    a.memory.remember_food(5, 2)
    a.memory.update_affinity("B", +1.2)
    a.energy = 5

    a.consider_goals(w)

    assert a.goal is not None
    assert a.goal.name == "EatThenGreet"


def test_goal_step_moves_toward_remembered_food():
    grid = Grid(10, 5)
    w = World(grid)
    a = Simulite("A", 2, 2, traits=Traits(curiosity=1, sociability=8))
    b = Simulite("B", 7, 2, traits=Traits(curiosity=1, sociability=8))
    w.add_agent(a)
    w.add_agent(b)

    a.memory.remember_food(5, 2)
    a.memory.update_affinity("B", +1.2)
    a.energy = 5

    a.consider_goals(w)
    assert a.goal is not None

    before = (a.x, a.y)
    acted = a.act_on_goal(w)
    after = (a.x, a.y)

    assert acted is True
    assert manhattan(after, (5, 2)) < manhattan(before, (5, 2))
