from simulai.core.world import World
from simulai.environment.grid import Grid
from simulai.environment.resources import Food
from simulai.agents.simulite import Simulite
from simulai.agents.traits import Traits

def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def test_chain_selected_when_hungry_and_food_remembered():
    grid = Grid(10, 5)
    w = World(grid)
    a = Simulite("A", 2, 2, traits=Traits(curiosity=1, sociability=8))
    b = Simulite("B", 7, 2, traits=Traits(curiosity=1, sociability=8))
    w.add_agent(a)
    w.add_agent(b)
    # conditions: hungry + remembered food + favorite friend present
    a.memory.remember_food(
