from simulai.agents.simulite import Simulite
from simulai.agents.traits import Traits
from simulai.core.world import World
from simulai.environment.grid import Grid
from simulai.environment.resources import Food


def test_food_increases_energy_and_mood():
    grid = Grid(5, 5)
    w = World(grid)
    # place Simulite with low energy next to food
    s = Simulite("A", 2, 2, traits=Traits(curiosity=1, sociability=1))
    w.add_agent(s)
    grid.place(3, 2, Food(energy=5))
    energy_before = s.energy
    mood_before = s.mood
    w.step()  # should move into food and eat
    assert s.energy > energy_before
    assert s.mood > mood_before


def test_social_interaction_affects_mood():
    grid = Grid(5, 5)
    w = World(grid)
    a = Simulite("A", 2, 2, traits=Traits(curiosity=1, sociability=8))
    b = Simulite("B", 3, 2, traits=Traits(curiosity=1, sociability=8))
    w.add_agent(a)
    w.add_agent(b)
    mood_a_before = a.mood
    w.step()  # adjacent + sociable -> interaction possible
    assert a.mood != mood_a_before  # mood should change (cheer or grumble)
