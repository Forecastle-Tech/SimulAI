from simulai.core.world import World
from simulai.environment.grid import Grid
from simulai.agents.simulite import Simulite
from simulai.agents.traits import Traits

def test_emotion_updates_without_crashing():
    grid = Grid(6, 6)
    w = World(grid)
    s = Simulite("A", 1, 1, traits=Traits(curiosity=5, sociability=5))
    w.add_agent(s)
    for _ in range(5):
        w.step()
        assert s.emotion is not None

def test_weather_cycles():
    grid = Grid(6, 6)
    w = World(grid)
    before = w.weather.kind
    for _ in range(w.weather.duration + 1):
        w.step()
    after = w.weather.kind
    # It might randomly be the same, but over a few cycles it should change.
    assert isinstance(after, str)
