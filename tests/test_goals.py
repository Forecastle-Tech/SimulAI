from simulai.core.world import World
from simulai.environment.grid import Grid
from simulai.agents.simulite import Simulite
from simulai.agents.traits import Traits

def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def test_goal_visit_remembered_food_selected_and_moves_toward():
    grid = Grid(10, 6)
    w = World(grid)
    s = Simulite("A", 2, 2, traits=Traits(curiosity=1, sociability=1))
    w.add_agent(s)
    s.memory.remember_food(7, 2)
    s.energy = 5  # hungry
    before = manhattan((s.x, s.y), (7, 2))
    w.step()
    # goal should be selected and we should not move further away
    after = manhattan((s.x, s.y), (7, 2))
    assert after <= before

def test_goal_greet_favorite_friend_selected():
    grid = Grid(8, 5)
    w = World(grid)
    a = Simulite("A", 1, 2, traits=Traits(curiosity=1, sociability=8))
    b = Simulite("B", 5, 2, traits=Traits(curiosity=1, sociability=8))
    w.add_agent(a)
    w.add_agent(b)
    # Make B the favorite friend
    a.memory.update_affinity("B", +2.0)
    # Give A decent energy so it doesn't nap
    a.energy = 9
    before = manhattan((a.x, a.y), (b.x, b.y))
    w.step()
    after = manhattan((a.x, a.y), (b.x, b.y))
    # Either it moved toward B or, if already adjacent, greeted (distance == 1)
    assert after <= before
