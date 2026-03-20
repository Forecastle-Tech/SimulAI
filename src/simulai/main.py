from __future__ import annotations

from simulai.agents.simulite import Simulite
from simulai.agents.traits import Traits
from simulai.core.world import World
from simulai.environment.grid import Grid
from simulai.render.pygame_renderer import PygameRenderer


def build_world() -> World:
    grid = Grid(10, 10)
    world = World(grid)

    # Create initial agents
    a = Simulite("A", 2, 2, traits=Traits(curiosity=4, sociability=7))
    b = Simulite("B", 7, 7, traits=Traits(curiosity=6, sociability=5))

    world.add_agent(a)
    world.add_agent(b)

    # Add initial food
    world.sprinkle_food(count=5)

    return world


def main():
    world = build_world()
    renderer = PygameRenderer(world.grid.width, world.grid.height)

    # Run simulation for 200 ticks
    for _ in range(200):
        world.step()
        renderer.render(world, fps=5)

    print("Simulation complete. Check outputs/simulation_metrics.csv")


if __name__ == "__main__":
    main()
